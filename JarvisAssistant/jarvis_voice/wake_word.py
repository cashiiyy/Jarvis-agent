"""
JarvisAssistant — Wake Word Listener
=====================================
Uses openwakeword as primary detector with a low threshold (0.35),
plus a Whisper-based fuzzy fallback when the score is borderline,
so casual/accented/soft speech reliably triggers the wake word.
"""
import logging
import pyaudio
import numpy as np
import openwakeword
from openwakeword.model import Model
from jarvis_core.event_bus import bus
import asyncio
import sys
import os

logger = logging.getLogger("jarvis.wake_word")

# Share wake_utils from voice_agent_hub (sibling directory)
_hub_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "voice_agent_hub")
)
if _hub_dir not in sys.path:
    sys.path.insert(0, _hub_dir)

try:
    from wake_utils import is_wake_word as _fuzzy_is_wake_word
    _HAS_WAKE_UTILS = True
except ImportError:
    _HAS_WAKE_UTILS = False
    logger.warning("wake_utils not found — fuzzy fallback disabled")


# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------
# Lower = more sensitive (catches soft/accented speech).
# 0.35 is a good balance; set lower (0.25) if still missing, higher if false positives.
OWW_THRESHOLD = 0.35

# Borderline range: if score is in [BORDERLINE_LOW, OWW_THRESHOLD) we run
# the fuzzy Whisper check before deciding.
BORDERLINE_LOW = 0.20


class JarvisWakeWord:
    def __init__(self):
        logger.info("Downloading / verifying openwakeword models...")
        openwakeword.utils.download_models()
        self.owwModel = Model(wakeword_models=["hey_jarvis"])
        logger.info("Wake-word model loaded (threshold=%.2f)", OWW_THRESHOLD)

        self.CHUNK = 1280
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000

        self.audio = pyaudio.PyAudio()
        self.mic_stream = None
        self.is_listening = False
        self._speaking = False     # True while TTS is playing → mute mic

        # Rolling 3-second audio buffer for borderline fuzzy check
        self._audio_buffer: list[np.ndarray] = []
        self._buffer_max_chunks = int(self.RATE * 3 / self.CHUNK)  # ~37 chunks

    # ------------------------------------------------------------------ #
    def _open_mic(self):
        if self.mic_stream is None or not self.mic_stream.is_active():
            self.mic_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
            )
            logger.debug("Mic stream opened")

    def _close_mic(self):
        if self.mic_stream and self.mic_stream.is_active():
            self.mic_stream.stop_stream()
            self.mic_stream.close()
            self.mic_stream = None
            logger.debug("Mic stream closed")

    def set_speaking(self, speaking: bool):
        """Called by TTS before/after playback to mute/unmute the mic."""
        self._speaking = speaking
        if speaking:
            self._close_mic()
        else:
            self._open_mic()

    # ------------------------------------------------------------------ #
    def _flush_buffer(self) -> np.ndarray:
        """Return a float32 audio array of the rolling buffer."""
        if not self._audio_buffer:
            return np.zeros(0, dtype=np.float32)
        combined = np.concatenate(self._audio_buffer).astype(np.float32) / 32768.0
        return combined

    def _borderline_fuzzy_check(self) -> bool:
        """
        Use the Whisper-based fuzzy matcher on the last 3 s of audio.
        Only called when OWW score is in the borderline range.
        """
        if not _HAS_WAKE_UTILS:
            return False
        try:
            # We need a WhisperModel — import lazily to avoid circular deps
            from faster_whisper import WhisperModel
            if not hasattr(self, "_whisper"):
                logger.info("Loading border-check Whisper model (tiny.en)...")
                self._whisper = WhisperModel("tiny.en", device="cpu", compute_type="int8")
            audio = self._flush_buffer()
            if len(audio) < self.RATE * 0.4:
                return False
            segments, _ = self._whisper.transcribe(audio, beam_size=1, vad_filter=True)
            text = " ".join(s.text for s in segments).strip()
            if not text:
                return False
            result = _fuzzy_is_wake_word(text)
            logger.debug("[Border] fuzzy check text='%s' result=%s", text, result)
            return result
        except Exception as exc:
            logger.debug("[Border] fuzzy check error: %s", exc)
            return False

    # ------------------------------------------------------------------ #
    async def listen_for_wake_word(self):
        self.is_listening = True
        self._open_mic()
        logger.info("Listening for wake word 'Hey Jarvis' (threshold=%.2f)...", OWW_THRESHOLD)
        print(f"\n[Wake] Listening for 'Hey Jarvis' (sensitivity={OWW_THRESHOLD:.2f})...")

        while self.is_listening:
            # Muted while TTS is speaking
            if self._speaking or self.mic_stream is None:
                await asyncio.sleep(0.05)
                continue

            try:
                raw = self.mic_stream.read(self.CHUNK, exception_on_overflow=False)
            except Exception:
                await asyncio.sleep(0.05)
                continue

            audio_data = np.frombuffer(raw, dtype=np.int16)

            # Maintain rolling buffer for borderline check
            self._audio_buffer.append(audio_data)
            if len(self._audio_buffer) > self._buffer_max_chunks:
                self._audio_buffer.pop(0)

            self.owwModel.predict(audio_data)

            triggered = False
            for mdl in self.owwModel.prediction_buffer.keys():
                scores = list(self.owwModel.prediction_buffer[mdl])
                score = scores[-1]

                if score >= OWW_THRESHOLD:
                    logger.info("[Wake] OWW score=%.3f >= threshold=%.2f → TRIGGERED", score, OWW_THRESHOLD)
                    print(f"[Wake] Wake word detected! (score={score:.3f})")
                    triggered = True
                    break

                elif BORDERLINE_LOW <= score < OWW_THRESHOLD:
                    # Borderline: run the fuzzy Whisper check in a thread
                    logger.debug("[Wake] borderline score=%.3f — running fuzzy check", score)
                    fuzzy_ok = await asyncio.to_thread(self._borderline_fuzzy_check)
                    if fuzzy_ok:
                        logger.info("[Wake] Fuzzy borderline check confirmed wake word (score=%.3f)", score)
                        print(f"[Wake] Wake word detected via fuzzy check! (score={score:.3f})")
                        triggered = True
                        break

            if triggered:
                self._close_mic()
                await bus.publish("WakeWordDetected")
                await asyncio.sleep(0.25)
                if not self._speaking:
                    self._open_mic()
                    self._audio_buffer.clear()

            await asyncio.sleep(0.01)

    def stop(self):
        self.is_listening = False
        self._close_mic()
        self.audio.terminate()
        logger.info("Wake word listener stopped")
