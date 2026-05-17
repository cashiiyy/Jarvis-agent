"""
main_orchestrator.py — JARVIS Voice Agent Hub
==============================================
Entry point for the standalone voice assistant.

Pipeline
--------
  Mic → VAD → Whisper(fast) → wake_utils.is_wake_word()
     → speak("Yes Sir ..?") → Mic → Whisper(full) → intent_router → ADB / pyautogui

Key fixes (v4)
--------------
  1. Wake-word: single shared is_wake_word() + cooldown + RMS debug logging
  2. Intent routing: "open <app>" WITHOUT a device keyword → defaults to PHONE
     (laptop actions must be explicitly prefixed with "on my laptop/pc/computer")
  3. Audio: persistent PyAudio stream with RMS-based VAD, noise floor learning,
     silence trimming, proper buffer chunking — no re-open on every call
  4. STT: initial_prompt for context, word-level timestamps off (faster),
     beam_size=3 for commands (balanced accuracy/speed)
"""
import os
import sys
import re
import time
import logging
import struct
import math
import subprocess
import threading
import urllib.parse
import webbrowser
from collections import deque
from typing import Optional

# ---------------------------------------------------------------------------
# Fix for missing cuBLAS / cuDNN dlls in CTranslate2 (Faster-Whisper)
# ---------------------------------------------------------------------------
_nvidia_base = os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages", "nvidia")
for _sub in ("cublas", "cudnn"):
    _bin = os.path.join(_nvidia_base, _sub, "bin")
    if os.path.exists(_bin) and _bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{_bin}{os.pathsep}" + os.environ.get("PATH", "")

import numpy as np
import pyaudio
from dotenv import load_dotenv
from faster_whisper import WhisperModel

# Local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wake_utils import is_wake_word, extract_inline_command          # noqa: E402
from android_launcher import adb_launch_app, adb_connect, adb_shell  # noqa: E402

# ── New intelligence layer (v5) ─────────────────────────────────────────────
from core.active_device_manager import get_device_manager            # noqa: E402
from core.context_memory        import get_memory                    # noqa: E402
from core.intent_classifier     import classify, Intent              # noqa: E402
from core.command_parser        import parse                         # noqa: E402
from skills.whatsapp_skill      import send_whatsapp_message         # noqa: E402
from skills.youtube_skill       import search_youtube                # noqa: E402

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("jarvis.orchestrator")
logging.getLogger("faster_whisper").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MOBILE_TARGET  = os.getenv("MOBILE_IP_PORT", "192.168.1.7:5555")
TABLET_TARGET  = os.getenv("TABLET_IP_PORT", "192.168.1.3:5555")

SAMPLE_RATE    = 16000
CHANNELS       = 1
CHUNK          = 1024           # frames per PyAudio read (~64 ms at 16 kHz)
FORMAT         = pyaudio.paInt16

# VAD thresholds
ENERGY_FLOOR   = 150            # RMS below this = silence (calibrated at start)
SPEECH_ONSET   = 1.5            # multiplier over floor to call it speech
SILENCE_SECS   = 0.9            # seconds of silence to end phrase
PRE_SPEECH_SECS = 4.0           # wait this long for speech to start
MAX_PHRASE_SECS = 10.0          # hard cap for a single phrase

# Wake-word cooldown — prevent retriggering within N seconds
WAKE_COOLDOWN_SECS = 2.0

# ---------------------------------------------------------------------------
# ANSI color helpers
# ---------------------------------------------------------------------------
COLOR_RESET  = "\033[0m"
COLOR_SYSTEM = "\033[93m"
COLOR_JARVIS = "\033[92m"
COLOR_USER   = "\033[96m"
COLOR_ERROR  = "\033[91m"
COLOR_DIM    = "\033[90m"


def _log(tag: str, msg: str, color: str = COLOR_SYSTEM):
    print(f"{color}[{tag}]{COLOR_RESET} {msg}")


# ---------------------------------------------------------------------------
# STT model
# ---------------------------------------------------------------------------
def _build_stt_model() -> WhisperModel:
    try:
        import ctranslate2
        if ctranslate2.get_supported_compute_types("cuda"):
            _log("System", "Loading Whisper -> GPU (float16)")
            return WhisperModel("base.en", device="cuda", compute_type="float16", num_workers=2)
    except Exception:
        pass
    _log("System", "Loading Whisper -> CPU (int8)")
    return WhisperModel("base.en", device="cpu", compute_type="int8", num_workers=2)


_log("System", "Initializing STT model...")
stt_model = _build_stt_model()
_log("System", "STT ready.", COLOR_JARVIS)

# Common noise/hallucination phrases Whisper emits on silence
_NOISE_PHRASES = {
    "", " ", ".", "..", "...", "thank you", "thanks", "you",
    "subtitles by", "blank audio", "okay", "test", "testing",
    "trial", "silence", "music", "applause", "laughter",
}


def _transcribe(audio: np.ndarray, beam_size: int = 3, initial_prompt: str = "") -> str:
    """Transcribe float32 [-1,1] audio. Returns cleaned text or empty string."""
    if len(audio) < SAMPLE_RATE * 0.3:   # shorter than 300 ms → ignore
        return ""
    # Trim silence from both ends before passing to Whisper
    audio = _trim_silence(audio)
    if len(audio) < SAMPLE_RATE * 0.2:
        return ""
    kwargs = dict(
        beam_size=beam_size,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=250, speech_pad_ms=200),
        without_timestamps=True,
        condition_on_previous_text=False,
    )
    if initial_prompt:
        kwargs["initial_prompt"] = initial_prompt
    segments, _ = stt_model.transcribe(audio, **kwargs)
    text = " ".join(s.text.strip() for s in segments).strip()
    if text.lower().strip(". ") in _NOISE_PHRASES:
        return ""
    return text


def _trim_silence(audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
    """Remove leading/trailing silence below threshold from float32 audio."""
    mask = np.abs(audio) > threshold
    if not np.any(mask):
        return audio
    start = int(np.argmax(mask))
    end   = int(len(mask) - np.argmax(mask[::-1]))
    # Keep 50 ms padding on each side
    pad = int(SAMPLE_RATE * 0.05)
    start = max(0, start - pad)
    end   = min(len(audio), end + pad)
    return audio[start:end]


# ---------------------------------------------------------------------------
# PyAudio — persistent stream for low-latency capture
# ---------------------------------------------------------------------------
_pa: Optional[pyaudio.PyAudio] = None
_stream: Optional[pyaudio.Stream] = None
_pa_lock = threading.Lock()


def _init_audio():
    global _pa, _stream
    with _pa_lock:
        if _pa is None:
            _pa = pyaudio.PyAudio()
        if _stream is None or not _stream.is_active():
            _stream = _pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK,
            )
            log.info("PyAudio stream opened (rate=%d, chunk=%d)", SAMPLE_RATE, CHUNK)


def _rms(data: bytes) -> float:
    """Root-mean-square of int16 PCM bytes."""
    if len(data) < 2:
        return 0.0
    count = len(data) // 2
    shorts = struct.unpack(f"{count}h", data[:count * 2])
    sq_sum = sum(s * s for s in shorts)
    return math.sqrt(sq_sum / count) if count else 0.0


# ---------------------------------------------------------------------------
# Noise-floor calibration
# ---------------------------------------------------------------------------
_energy_floor = ENERGY_FLOOR   # updated during calibration


def calibrate_mic(duration: float = 2.5):
    """Measure ambient RMS over `duration` seconds and set the speech onset."""
    global _energy_floor
    _init_audio()
    _log("System", f"Calibrating mic — stay quiet for {duration:.0f} s...")
    frames = []
    chunks_needed = int(SAMPLE_RATE / CHUNK * duration)
    with _pa_lock:
        for _ in range(chunks_needed):
            frames.append(_stream.read(CHUNK, exception_on_overflow=False))
    rms_values = [_rms(f) for f in frames]
    ambient = float(np.mean(rms_values)) if rms_values else ENERGY_FLOOR
    # Noise floor = ambient + 20 % headroom, but never below 100
    _energy_floor = max(100.0, ambient * 1.2)
    speech_trigger = _energy_floor * SPEECH_ONSET
    _log("System",
         f"Calibration done. Floor={_energy_floor:.1f}  SpeechTrigger={speech_trigger:.1f}",
         COLOR_JARVIS)


# ---------------------------------------------------------------------------
# VAD-based microphone capture (uses persistent stream)
# ---------------------------------------------------------------------------
def record_phrase(
    max_secs: float = MAX_PHRASE_SECS,
    pre_speech_secs: float = PRE_SPEECH_SECS,
    silence_secs: float = SILENCE_SECS,
    prompt: str = "",
) -> np.ndarray:
    """
    Record until speech ends or limits hit.
    Returns float32 array in [-1, 1].

    Debug output:
      · Prints RMS for each chunk when logging level is DEBUG.
      · Prints onset/silence events at INFO.
    """
    _init_audio()
    if prompt:
        _log("System", prompt)

    frames: list[bytes] = []
    speech_started = False
    silence_start: Optional[float] = None
    start_time = time.time()
    speech_trigger = _energy_floor * SPEECH_ONSET

    while True:
        elapsed = time.time() - start_time

        with _pa_lock:
            data = _stream.read(CHUNK, exception_on_overflow=False)

        rms = _rms(data)
        log.debug("[MIC] RMS=%.1f  trigger=%.1f  elapsed=%.2fs", rms, speech_trigger, elapsed)

        if not speech_started:
            if rms >= speech_trigger:
                speech_started = True
                silence_start = None
                frames.append(data)
                log.info("[VAD] Speech onset detected (RMS=%.1f)", rms)
                _log("System", f"Recording... (RMS={rms:.0f})", COLOR_DIM)
            elif elapsed > pre_speech_secs:
                log.info("[VAD] No speech detected after %.1fs", pre_speech_secs)
                return np.array([], dtype=np.float32)
        else:
            frames.append(data)
            if rms < speech_trigger:
                if silence_start is None:
                    silence_start = time.time()
                    log.debug("[VAD] Silence started")
                elif time.time() - silence_start >= silence_secs:
                    log.info("[VAD] Silence %.1fs → end of phrase", silence_secs)
                    break
            else:
                if silence_start is not None:
                    log.debug("[VAD] Speech resumed")
                silence_start = None

        if elapsed >= max_secs:
            log.info("[VAD] Max duration %.1fs reached", max_secs)
            break

    if not frames:
        return np.array([], dtype=np.float32)

    raw = b"".join(frames)
    audio_np = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    log.info("[VAD] Captured %.2f s of audio (frames=%d)", len(audio_np) / SAMPLE_RATE, len(frames))
    return audio_np


# ---------------------------------------------------------------------------
# TTS (console-only for now, XTTS disabled for stability)
# ---------------------------------------------------------------------------
def speak(text: str):
    if text:
        print(f"\n{COLOR_JARVIS}[Jarvis]:{COLOR_RESET} {text}")


# ---------------------------------------------------------------------------
# Intent classifier — decides if a command is phone-targeted
# ---------------------------------------------------------------------------
# These app names are phone-native; if said without a device prefix,
# assume the user wants their phone, NOT a browser/laptop.
_PHONE_NATIVE_APPS = {
    "whatsapp", "instagram", "snapchat", "tiktok", "telegram",
    "spotify", "netflix", "prime", "hotstar", "zee5", "gaana",
    "youtube", "facebook", "twitter", "x", "discord", "signal",
    "zoom", "phonepe", "paytm", "gpay", "google pay", "bhim",
    "swiggy", "zomato", "ola", "uber", "rapido", "flipkart",
    "amazon", "meesho", "myntra", "bigbasket", "blinkit",
    "insta",  "fb", "tg", "yt",    # short aliases
}

# Explicit laptop-only trigger words
_LAPTOP_TRIGGERS = re.compile(
    r"\bon my\s+(laptop|computer|pc|windows|desktop)\b", re.IGNORECASE
)
_PHONE_TRIGGERS = re.compile(
    r"\bon my\s+(phone|mobile|android|handset)\b", re.IGNORECASE
)
_TABLET_TRIGGERS = re.compile(
    r"\bon my\s+(tablet|tab|ipad)\b", re.IGNORECASE
)


def _classify_device(intent: str) -> str:
    """
    Return 'phone', 'tablet', or 'laptop' based on context.

    Logic:
      1. Explicit "on my phone/tablet/laptop" → direct mapping
      2. Command contains a phone-native app name AND no laptop prefix → phone
      3. Everything else → laptop
    """
    lower = intent.lower()

    if _LAPTOP_TRIGGERS.search(lower):
        return "laptop"
    if _PHONE_TRIGGERS.search(lower):
        return "phone"
    if _TABLET_TRIGGERS.search(lower):
        return "tablet"

    # Check if any phone-native app is mentioned
    words = re.sub(r"[^\w\s]", " ", lower).split()
    # Also check 2-word combos like "prime video", "google pay"
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
    for token in words + bigrams:
        if token in _PHONE_NATIVE_APPS:
            log.info("[Router] Phone-native app '%s' detected -> routing to phone", token)
            return "phone"

    return "laptop"


def _strip_device_phrases(text: str) -> str:
    """Remove device-routing phrases so the clean action remains."""
    t = _LAPTOP_TRIGGERS.sub("", text)
    t = _PHONE_TRIGGERS.sub("", t)
    t = _TABLET_TRIGGERS.sub("", t)
    return re.sub(r"\s{2,}", " ", t).strip()


# ---------------------------------------------------------------------------
# Laptop execution
# ---------------------------------------------------------------------------
_LAPTOP_APPS = {
    "whatsapp":   "whatsapp:",
    "youtube":    "https://www.youtube.com",
    "chrome":     "chrome",
    "notepad":    "notepad",
    "calculator": "calc",
    "settings":   "ms-settings:",
    "spotify":    "spotify:",
    "discord":    "discord:",
    "telegram":   "telegram:",
    "camera":     "microsoft.windows.camera:",
    "photos":     "ms-photos:",
    "mail":       "ms-outlook:",
    "paint":      "mspaint",
    "vlc":        "vlc",
    "word":       "winword",
    "excel":      "excel",
    "powerpoint": "powerpnt",
}


def _open_laptop_app(app_name: str):
    name = app_name.strip().lower()
    target = _LAPTOP_APPS.get(name)
    if target:
        if target.startswith("http"):
            webbrowser.open(target)
        elif ":" in target:
            subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)
        else:
            subprocess.Popen(["cmd", "/c", "start", target], shell=False)
        log.info("[Laptop] Opened '%s'", app_name)
    else:
        import pyautogui
        log.info("[Laptop] Start menu search for '%s'", app_name)
        pyautogui.press("win")
        time.sleep(0.6)
        pyautogui.write(app_name, interval=0.04)
        time.sleep(0.5)
        pyautogui.press("enter")


def execute_on_laptop(intent_text: str):
    speak("Right away, sir.")
    intent = intent_text.lower().strip()

    m = re.search(r"(?:open|launch|start)\s+(.+)", intent)
    if m:
        app = re.sub(r"\s*(app|application)$", "", m.group(1)).strip()
        _open_laptop_app(app)
        return

    m = re.search(r"search(?:\s+for)?\s+(.+)", intent)
    if m:
        query = m.group(1).strip()
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}")
        log.info("[Laptop] Web search: '%s'", query)
        return

    log.warning("[Laptop] No handler for '%s' — trying Start menu", intent_text)
    _open_laptop_app(intent_text)


# ---------------------------------------------------------------------------
# Android execution
# ---------------------------------------------------------------------------
def execute_on_android(intent_text: str, device_ip: str, device_label: str):
    intent = intent_text.lower().strip()
    log.info("[Android] Intent='%s'  device=%s  ip=%s", intent_text, device_label, device_ip)

    speak(f"On it, sir.")

    connected = adb_connect(device_ip)
    if not connected:
        speak(f"I can't reach your {device_label}. Check Wi-Fi and wireless ADB.")
        log.error("[Android] Cannot connect to %s (%s)", device_label, device_ip)
        return

    # Launch app
    m = re.search(r"(?:open|launch|start|run|show|play)\s+(.+)", intent)
    if m:
        app = re.sub(r"\s*(app|application)$", "", m.group(1)).strip()
        log.info("[Android] Launching app '%s' on %s", app, device_label)
        success, message = adb_launch_app(device_ip, app)
        log.info("[Android] Launch result: success=%s  msg=%s", success, message)
        speak(message)
        return

    # Web search on device
    m = re.search(r"search(?:\s+for)?\s+(.+)", intent)
    if m:
        query = m.group(1).strip()
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        ok, _, err = adb_shell(device_ip, f"am start -a android.intent.action.VIEW -d '{url}'")
        log.info("[Android] Browser search '%s' — ok=%s", query, ok)
        if ok:
            speak(f"Searching for {query} on your {device_label}.")
        else:
            speak(f"Could not open the browser on your {device_label}.")
        return

    log.warning("[Android] No handler for '%s'", intent_text)
    speak(f"I'm not sure how to do that on your {device_label}.")


# ---------------------------------------------------------------------------
# Command router v5  — intent + parser + device manager + context memory
# ---------------------------------------------------------------------------
def route_command(raw: str):
    """
    Smart routing pipeline (v5)
    Priority: explicit device > active_device_manager > phone-native heuristic
    """
    mem     = get_memory()
    dev_mgr = get_device_manager()

    # Intent classification
    intent = classify(raw)
    log.info("[Router] Intent=%s  raw='%s'", intent.value, raw[:60])

    # Device-switch
    if intent == Intent.DEVICE_SWITCH:
        new_label = dev_mgr.detect_set_command(raw)
        speak(f"Default device changed to {new_label}." if new_label else "Device not recognised.")
        if new_label:
            mem.update(device=dev_mgr.active)
        return

    # Device-query
    if intent == Intent.DEVICE_QUERY:
        speak(dev_mgr.query_response())
        return

    # Parse entities
    cmd = parse(raw)

    # Multi-step: split on 'and/then/after that' and execute each step
    if intent == Intent.MULTISTEP and len(cmd.steps) > 1:
        _log("Router", f"Multi-step: {len(cmd.steps)} steps", COLOR_SYSTEM)
        for i, step in enumerate(cmd.steps, 1):
            _log("Step", f"{i}/{len(cmd.steps)}: {step}", COLOR_JARVIS)
            route_command(step)
            if i < len(cmd.steps):
                time.sleep(2.5)
        return

    # Resolve target device
    if cmd.device_target:
        target_device = cmd.device_target
    elif mem.last_device:
        target_device = mem.last_device
    else:
        target_device = _classify_device(raw)
        if target_device == "laptop" and dev_mgr.active != "laptop":
            target_device = dev_mgr.active

    dev_ip = MOBILE_TARGET if target_device == "phone" else TABLET_TARGET
    _log("Router", f"device={target_device!r}  intent={intent.value}", COLOR_SYSTEM)

    # Fill from context memory
    app, _, contact, query = mem.fill_gaps(
        app=cmd.app_target, contact=cmd.contact_name, query=cmd.search_query)

    # SEND_MESSAGE
    if intent == Intent.SEND_MESSAGE:
        contact = cmd.contact_name or contact
        message = cmd.message_body or ""
        if not contact:
            speak("Who should I send the message to?")
            return
        if not message:
            speak(f"What should I say to {contact}?")
            return
        if target_device in ("phone", "tablet"):
            speak(f"Sending message to {contact} via WhatsApp.")
            ok, result = send_whatsapp_message(dev_ip, contact, message)
            speak(result)
            if ok:
                mem.update(app="whatsapp", device=target_device, contact=contact)
        else:
            speak("Messaging is only supported on Android devices.")
        return

    # OPEN_APP
    if intent in (Intent.OPEN_APP, Intent.UNKNOWN) and cmd.action in (
            "open", "launch", "start", "run", "show", "play", None):
        app_name = cmd.app_target or app
        if not app_name:
            _log("Router", f"Fallback — no app parsed, raw='{raw}'", COLOR_ERROR)
        else:
            speak(f"Opening {app_name} on your {target_device}.")
            if target_device == "laptop":
                execute_on_laptop(f"open {app_name}")
            elif app_name in ("youtube", "yt") and query:
                ok, msg = search_youtube(dev_ip, query)
                speak(msg)
                mem.update(app="youtube", device=target_device, query=query)
                return
            else:
                execute_on_android(f"open {app_name}", dev_ip, target_device)
            mem.update(app=app_name, device=target_device)
            return

    # SEARCH
    if intent == Intent.SEARCH:
        q = cmd.search_query or query or raw
        speak(f"Searching for {q}.")
        if target_device in ("phone", "tablet"):
            if mem.last_app in ("youtube", "yt"):
                ok, msg = search_youtube(dev_ip, q)
                speak(msg)
            else:
                execute_on_android(f"search {q}", dev_ip, target_device)
        else:
            execute_on_laptop(f"search {q}")
        mem.update(query=q)
        return

    # Fallback
    clean = _strip_device_phrases(raw)
    _log("Router", f"Fallback -> device={target_device!r}  cmd={clean!r}", COLOR_SYSTEM)
    if target_device == "laptop":
        execute_on_laptop(clean)
    elif target_device == "phone":
        execute_on_android(clean, MOBILE_TARGET, "phone")
    else:
        execute_on_android(clean, TABLET_TARGET, "tablet")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main_loop():
    print(f"\n{COLOR_SYSTEM}{'='*52}{COLOR_RESET}")
    print(f"{COLOR_JARVIS}        JARVIS VOICE AGENT HUB — ONLINE          {COLOR_RESET}")
    print(f"{COLOR_SYSTEM}  Phone  : {MOBILE_TARGET}")
    print(f"  Tablet : {TABLET_TARGET}")
    print(f"{'='*52}{COLOR_RESET}\n")

    calibrate_mic()
    speak("Systems online. Say 'Hey Jarvis' to activate.")

    _last_wake_time = 0.0   # cooldown tracker

    while True:
        try:
            # ── Stage 1: Wake-word phrase ─────────────────────────────────────
            audio = record_phrase(
                max_secs=8.0,
                pre_speech_secs=PRE_SPEECH_SECS,
                silence_secs=0.7,
                prompt="Listening for 'Hey Jarvis'...",
            )
            if len(audio) == 0:
                continue

            # Fast beam_size=1 for lowest latency on wake detection
            transcription = _transcribe(audio, beam_size=1,
                                         initial_prompt="Hey Jarvis")
            if not transcription:
                continue

            _log("Heard", transcription, COLOR_USER)
            log.debug("[Wake] raw text: '%s'", transcription)

            # Cooldown — skip if triggered too recently
            now = time.time()
            if is_wake_word(transcription):
                if now - _last_wake_time < WAKE_COOLDOWN_SECS:
                    log.info("[Wake] Cooldown active — skipping duplicate trigger")
                    continue
                _last_wake_time = now

                _log("System", "Wake word detected!", COLOR_JARVIS)
                log.info("[Wake] Triggered by: '%s'", transcription)

                # Check for inline command ("Hey Jarvis open WhatsApp")
                inline = extract_inline_command(transcription)

                if inline and len(inline.split()) >= 2:
                    _log("Intent", inline, COLOR_USER)
                    log.info("[Intent] Inline command: '%s'", inline)
                    route_command(inline)
                    speak("Anything else, sir?")
                else:
                    # No inline command → acknowledge and record command
                    speak("Yes Sir ..?")
                    _log("System", "Awaiting command...", COLOR_SYSTEM)

                    cmd_audio = record_phrase(
                        max_secs=12.0,
                        pre_speech_secs=6.0,
                        silence_secs=SILENCE_SECS,
                        prompt="",
                    )

                    if len(cmd_audio) == 0:
                        speak("I didn't catch that.")
                        continue

                    # Full accuracy transcription for command
                    cmd_text = _transcribe(
                        cmd_audio, beam_size=3,
                        initial_prompt="Open WhatsApp Instagram YouTube Spotify"
                    )

                    if not cmd_text:
                        speak("I didn't catch that. Please try again.")
                        continue

                    _log("Intent", cmd_text, COLOR_USER)
                    log.info("[Intent] Command: '%s'", cmd_text)

                    if re.search(r"\b(shut down|exit|stop|goodbye|bye)\b",
                                 cmd_text.lower()):
                        speak("Shutting down. Goodbye, sir.")
                        break

                    route_command(cmd_text)
                    speak("Anything else, sir?")

            else:
                log.debug("[Wake] Not a wake word: '%s'", transcription)
                _log("System", f"(not wake word — heard: {transcription!r})", COLOR_DIM)

        except KeyboardInterrupt:
            _log("System", "\nStopped by user.")
            break
        except Exception as exc:
            log.exception("[Main] Unexpected error: %s", exc)
            time.sleep(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main_loop()
