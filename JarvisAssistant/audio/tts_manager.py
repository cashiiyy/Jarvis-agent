"""
audio/tts_manager.py  —  JARVIS Coqui XTTS Singleton TTS Manager
=================================================================
Loads the locally trained XTTS model ONCE on startup.
Exposes a thread-safe speak() function used by every module.

Design rules (per task spec):
  · Model loaded once → stays in memory (singleton pattern).
  · FIFO speech queue → no overlapping / race conditions.
  · Audio caching for frequent short phrases.
  · Fails gracefully → JARVIS continues on TTS crash.
  · Uses sounddevice (already in project) for playback.
  · Does NOT interfere with the mic / wake-word pipeline.
"""

from __future__ import annotations

import hashlib
import io
import logging
import os
import queue
import threading
import time
from typing import Optional

import numpy as np

# ---------------------------------------------------------------------------
# Lazy imports – avoid loading heavy libs until _TTSManager initialises
# ---------------------------------------------------------------------------
_sd = None          # sounddevice
_torch = None       # torch
_resample_poly = None  # scipy.signal.resample_poly

log = logging.getLogger("jarvis.tts_manager")

# ---------------------------------------------------------------------------
# Read config from environment / tts_settings (populated by config.py)
# ---------------------------------------------------------------------------
def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


# ---------------------------------------------------------------------------
# Internal TTS Manager (singleton)
# ---------------------------------------------------------------------------
class _TTSManager:
    """
    Singleton that owns the XTTS model and a background speech-worker thread.
    """

    _instance: Optional[_TTSManager] = None
    _lock = threading.Lock()

    # ------------------------------------------------------------------ #
    def __init__(self, settings: dict):
        self._settings = settings
        self._model = None
        self._xtts_config = None
        self._loaded = False
        self._load_error: Optional[str] = None

        # pyttsx3 SAPI engine — used as emergency fallback when XTTS fails
        self._sapi = None
        try:
            import pyttsx3 as _pyttsx3
            _eng = _pyttsx3.init()
            voices = _eng.getProperty("voices")
            for v in voices:
                if "david" in v.name.lower() or "mark" in v.name.lower():
                    _eng.setProperty("voice", v.id)
                    break
            _eng.setProperty("rate", 185)
            _eng.setProperty("volume", 0.92)
            self._sapi = _eng
            print("[TTS] SAPI fallback engine ready")
        except Exception:
            pass  # pyttsx3 not available — will be silent on XTTS failure

        # Playback lock — only one sd.play() at a time
        self._playback_lock = threading.Lock()

        # FIFO speech queue (unlimited depth; each item is a str)
        self._speech_queue: queue.Queue[str] = queue.Queue()

        # Audio cache: phrase_hash → np.ndarray (float32)
        self._audio_cache: dict[str, np.ndarray] = {}
        self._cache_lock = threading.Lock()

        # Device sample rate (resolved once)
        self._device_samplerate: int = settings.get("sample_rate", 24000)

        # Speaking flag – can be read by wake-word listener
        self._is_speaking = False
        self._speaking_callbacks: list = []

        # Start worker thread
        self._worker = threading.Thread(
            target=self._speech_worker, daemon=True, name="JarvisTTSWorker"
        )
        self._worker.start()

        # Load model (blocking, runs on the calling thread so startup logs are ordered)
        self._load_model()

    # ------------------------------------------------------------------ #
    #  Model loading
    # ------------------------------------------------------------------ #
    def _load_model(self):
        global _torch, _sd, _resample_poly
        settings = self._settings

        # Resolve device
        try:
            import torch as _t
            _torch = _t
            if settings.get("use_gpu", True) and _torch.cuda.is_available():
                self._device = "cuda"
                print("[TTS] Using CUDA")
            else:
                self._device = "cpu"
                print("[TTS] Using CPU fallback")
        except Exception as e:
            self._device = "cpu"
            print(f"[TTS] torch import failed ({e}); defaulting to CPU")

        # Import sounddevice
        try:
            import sounddevice as _sdev
            _sd = _sdev
            di = _sdev.query_devices(kind="output")
            sr = int(di.get("default_samplerate") or settings.get("sample_rate", 24000))
            self._device_samplerate = sr if sr > 0 else settings.get("sample_rate", 24000)
        except Exception:
            pass

        # Import scipy resample
        try:
            from scipy.signal import resample_poly as _rp
            _resample_poly = _rp
        except Exception:
            pass

        # Validate paths
        model_dir   = settings.get("model_dir", "")
        config_path = settings.get("config_path", "")
        speaker_wav = settings.get("speaker_wav", "")
        checkpoint  = settings.get("checkpoint_path", "")
        vocab_path  = settings.get("vocab_path", "")

        missing = []
        if not model_dir or not os.path.isdir(model_dir):
            missing.append(f"model_dir: {model_dir!r}")
        if not config_path or not os.path.isfile(config_path):
            missing.append(f"config_path: {config_path!r}")
        if not speaker_wav or not os.path.isfile(speaker_wav):
            missing.append(f"speaker_wav: {speaker_wav!r}")
        if not checkpoint or not os.path.isfile(checkpoint):
            missing.append(f"checkpoint_path: {checkpoint!r}")

        if missing:
            self._load_error = f"Missing assets: {'; '.join(missing)}"
            print(f"[TTS ERROR] {self._load_error}")
            return

        if vocab_path and not os.path.isfile(vocab_path):
            print(f"[TTS] Warning: vocab_path not found at {vocab_path!r} — will skip")
            vocab_path = ""

        # Load XTTS
        try:
            from TTS.tts.configs.xtts_config import XttsConfig
            from TTS.tts.models.xtts import Xtts
            import TTS.tts.models.xtts as _xtts_module

            # ── Monkey-patch load_audio to bypass torchcodec ──────────────────
            # torchcodec 0.12 DLLs are incompatible with the nightly PyTorch
            # build (2.12.0.dev+cu128). Use soundfile + librosa instead.
            # This is the same approach used in the project's test_xtts.py.
            try:
                import soundfile as _sf
                import librosa as _librosa

                def _patched_load_audio(audiopath, sampling_rate):
                    wav, sr_orig = _sf.read(audiopath, dtype="float32")
                    if wav.ndim > 1:
                        wav = wav.mean(axis=1)  # stereo → mono
                    if sr_orig != sampling_rate:
                        wav = _librosa.resample(wav, orig_sr=sr_orig, target_sr=sampling_rate)
                    wav = wav.clip(-1.0, 1.0)
                    return _torch.tensor(wav).unsqueeze(0).float()

                _xtts_module.load_audio = _patched_load_audio
                print("[TTS] load_audio patched -> soundfile+librosa (torchcodec bypassed)")
            except ImportError as _patch_err:
                print(f"[TTS] Warning: could not patch load_audio ({_patch_err}); torchcodec may be needed")

            # ── Monkey-patch GPT2InferenceModel for transformers 4.32+ ────────
            # transformers added _validate_model_class() (called inside generate())
            # which raises TypeError if can_generate() returns False.
            # GPT2InferenceModel is a custom class not in the official registry
            # so both checks fail. Fix with three layers:
            #   1. _validate_model_class -> no-op  (what generate() actually calls)
            #   2. can_generate           -> True   (backup)
            #   3. _supports_generate     -> True   (some versions check this attr)
            try:
                from TTS.tts.layers.tortoise.autoregressive import GPT2InferenceModel

                # Layer 1 — nuke the validation method entirely (most reliable)
                GPT2InferenceModel._validate_model_class = lambda self: None

                # Layer 2 — override can_generate classmethod
                @classmethod
                def _cg(cls):
                    return True
                GPT2InferenceModel.can_generate = _cg

                # Layer 3 — attribute fallback used by some transformers builds
                GPT2InferenceModel._supports_generate = True

                print("[TTS] GPT2InferenceModel generate() patches applied")
            except Exception as _cg_err:
                print(f"[TTS] Warning: could not patch GPT2InferenceModel ({_cg_err})")

            # ── Nuclear option: patch GenerationMixin globally ────────────────
            # _validate_model_class is the method generate() actually calls.
            # Patching it on the base class ensures no version of transformers
            # can block synthesis regardless of subclass resolution order.
            try:
                from transformers import GenerationMixin
                GenerationMixin._validate_model_class = lambda self: None
                print("[TTS] GenerationMixin._validate_model_class patched globally")
            except Exception as _gm_err:
                print(f"[TTS] Warning: could not patch GenerationMixin ({_gm_err})")

            # ── Patch GenerationMixin.prepare_inputs_for_generation ────────────
            # The base method raises NotImplementedError. Any concrete class that
            # doesn't override it crashes generate(). Since GPT2InferenceModel
            # is resolved through the XTTS model nesting and our class-level
            # patch may not be reached, patch the base directly.
            try:
                from transformers import GenerationMixin

                def _safe_pifg(self, input_ids, past_key_values=None, **kwargs):
                    if past_key_values is not None:
                        input_ids = input_ids[:, -1].unsqueeze(-1)
                    return {
                        "input_ids": input_ids,
                        "past_key_values": past_key_values,
                        "use_cache": kwargs.get("use_cache", True),
                        "attention_mask": kwargs.get("attention_mask", None),
                    }

                # Only replace if the base still raises (don't break other models)
                import inspect as _inspect
                _src = _inspect.getsource(GenerationMixin.prepare_inputs_for_generation)
                if "NotImplementedError" in _src:
                    GenerationMixin.prepare_inputs_for_generation = _safe_pifg
                    print("[TTS] GenerationMixin.prepare_inputs_for_generation patched (NotImplementedError guard)")
            except Exception as _pifg_err:
                print(f"[TTS] Warning: could not patch prepare_inputs_for_generation ({_pifg_err})")

            # ── Patch _prepare_generation_config to guard against None ────────
            # inference_model is created lazily inside inference_speech() so
            # post-load patching of generation_config never reaches it.
            # generation_config is None when can_generate() returned False at
            # construction time. Guard it in the method that generate() calls.
            try:
                from transformers import GenerationMixin, GenerationConfig
                _orig_pgc = GenerationMixin._prepare_generation_config

                def _safe_pgc(self, generation_config, **kwargs):
                    if getattr(self, "generation_config", None) is None:
                        self.generation_config = GenerationConfig()
                    return _orig_pgc(self, generation_config, **kwargs)

                GenerationMixin._prepare_generation_config = _safe_pgc
                print("[TTS] GenerationMixin._prepare_generation_config patched (None guard)")
            except Exception as _pgc_err:
                print(f"[TTS] Warning: could not patch _prepare_generation_config ({_pgc_err})")

            # PyTorch 2.6+ requires safe globals for deserialization
            try:
                from TTS.tts.models.xtts import XttsArgs, XttsAudioConfig
                from TTS.config.shared_configs import BaseDatasetConfig
                _torch.serialization.add_safe_globals([
                    XttsConfig, XttsAudioConfig, XttsArgs, BaseDatasetConfig
                ])
            except Exception:
                pass  # Older PyTorch / older TTS — not needed

            xtts_cfg = XttsConfig()
            xtts_cfg.load_json(config_path)
            self._xtts_config = xtts_cfg

            model = Xtts.init_from_config(xtts_cfg)
            try:
                model.load_checkpoint(
                    xtts_cfg,
                    checkpoint_dir=model_dir,
                    checkpoint_path=checkpoint,
                    vocab_path=vocab_path if vocab_path else None,
                    eval=True,
                    strict=False,
                )
            except Exception as e:
                log.warning("[TTS] load_checkpoint() failed, trying compat loader: %s", e)
                self._load_checkpoint_compat(model, checkpoint)

            # Move to device
            try:
                model.to(self._device)
                model.eval()
            except RuntimeError as e:
                err_lower = str(e).lower()
                if self._device == "cuda" and ("no kernel" in err_lower or "cuda" in err_lower):
                    print("[TTS] CUDA unsupported — falling back to CPU")
                    self._device = "cpu"
                    model.to("cpu")
                    model.eval()
                else:
                    raise

            self._model = model
            self._loaded = True

            # ── Fix generation_config on the inference model ──────────────────
            # PreTrainedModel.__init__ sets generation_config = None when
            # can_generate() returns False at construction time (before our patch).
            # transformers 4.39 generate() then crashes on None._from_model_config.
            # Fix: explicitly set it now that the model is fully loaded.
            try:
                from transformers import GenerationConfig
                inf_model = getattr(getattr(model, "gpt", None), "inference_model", None)
                if inf_model is not None and getattr(inf_model, "generation_config", None) is None:
                    inf_model.generation_config = GenerationConfig()
                    print("[TTS] inference_model.generation_config initialised")
            except Exception as _gc_err:
                print(f"[TTS] Warning: could not fix generation_config ({_gc_err})")

            print(f"[TTS] Model loaded successfully (device={self._device}, sr={self._device_samplerate})")

        except Exception as e:
            self._load_error = str(e)
            print(f"[TTS ERROR] Model failed to load: {e}")
            log.exception("[TTS] Model loading exception")

    # ------------------------------------------------------------------ #
    def _load_checkpoint_compat(self, model, checkpoint_path: str):
        """Compatibility loader for custom fine-tuned checkpoints."""
        ckpt = _torch.load(checkpoint_path, map_location="cpu")
        state_dict = ckpt.get("model", ckpt)
        remapped = {}
        for k, v in state_dict.items():
            nk = k
            if nk.startswith("xtts."):
                nk = nk[5:]
            nk = nk.replace("gpt.gpt_inference.", "gpt.gpt.")
            remapped[nk] = v
        missing, unexpected = model.load_state_dict(remapped, strict=False)
        log.info("[TTS] Compat load: missing=%d, unexpected=%d", len(missing), len(unexpected))

    # ------------------------------------------------------------------ #
    #  Background speech worker
    # ------------------------------------------------------------------ #
    def _speech_worker(self):
        """Processes queued speech requests sequentially (FIFO)."""
        while True:
            try:
                text = self._speech_queue.get(block=True, timeout=1.0)
                self._synthesise_and_play(text)
                self._speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                log.error("[TTS Worker] Unexpected error: %s", e)

    # ------------------------------------------------------------------ #
    #  Core synthesis + playback
    # ------------------------------------------------------------------ #
    def _synthesise_and_play(self, text: str):
        """Generate audio and play it. Falls back to SAPI if XTTS fails."""
        if not text or not text.strip():
            return

        self._set_speaking(True)
        try:
            audio = self._get_audio(text)
            if audio is not None and len(audio) > 0:
                with self._playback_lock:
                    self._play(audio)
            else:
                # XTTS returned nothing — fall back to SAPI so Jarvis is never silent
                self._speak_sapi_fallback(text)
        except Exception as e:
            log.error("[TTS] Playback error: %s", e)
            self._speak_sapi_fallback(text)
        finally:
            self._set_speaking(False)

    def _speak_sapi_fallback(self, text: str):
        """Emergency SAPI/pyttsx3 fallback — Jarvis always speaks something."""
        if self._sapi is None:
            return
        try:
            self._sapi.say(text)
            self._sapi.runAndWait()
            log.info("[TTS] SAPI fallback used for: %r", text[:40])
        except Exception as e:
            log.error("[TTS] SAPI fallback also failed: %s", e)

    def _get_audio(self, text: str) -> Optional[np.ndarray]:
        """Return synthesised audio (float32). Uses cache for repeated phrases."""
        cache_key = hashlib.md5(text.lower().strip().encode()).hexdigest()

        with self._cache_lock:
            if cache_key in self._audio_cache:
                log.debug("[TTS] Cache hit for: %r", text[:40])
                return self._audio_cache[cache_key]

        audio = self._synthesise(text)

        if audio is not None:
            with self._cache_lock:
                # Cap cache at 50 entries to avoid memory bloat
                if len(self._audio_cache) >= 50:
                    oldest_key = next(iter(self._audio_cache))
                    del self._audio_cache[oldest_key]
                self._audio_cache[cache_key] = audio

        return audio

    def _synthesise(self, text: str) -> Optional[np.ndarray]:
        """Run XTTS inference and return post-processed float32 audio."""
        if not self._loaded or self._model is None:
            print(f"[TTS ERROR] Model not loaded — cannot speak: {text!r}")
            return None

        settings = self._settings
        speaker_wav = settings.get("speaker_wav", "")
        language = settings.get("language", "en")

        clean = self._clean_text(text)

        synth_kwargs: dict = {}
        if settings.get("use_fast_inference", True):
            synth_kwargs = {
                "gpt_cond_len":  settings.get("gpt_cond_len", 1),
                "top_k":         settings.get("top_k", 20),
                "top_p":         settings.get("top_p", 0.75),
                "temperature":   settings.get("temperature", 0.45),
            }


        try:
            t0 = time.perf_counter()
            with _torch.inference_mode():
                out = self._model.synthesize(
                    text=clean,
                    speaker_wav=speaker_wav,
                    language=language,
                    **synth_kwargs,
                )
            log.info("[TTS] Inference %.0f ms — %r", (time.perf_counter() - t0) * 1000, text[:40])
            return self._postprocess(np.array(out["wav"], dtype=np.float32))

        except Exception as e:
            err = str(e).lower()
            log.error("[TTS ERROR] Synthesis failed: %s", e)

            # GPT2InferenceModel generate() / generation_config errors — fix and retry
            if (
                "not compatible with" in err
                or "language model head" in err
                or "_from_model_config" in err
                or "nonetype" in err
            ):
                try:
                    log.warning("[TTS] Applying runtime generation fixes and retrying...")
                    from transformers import GenerationConfig
                    gpt_model = getattr(self._model, "gpt", None)
                    inf_model = getattr(gpt_model, "inference_model", None) if gpt_model else None
                    if inf_model is not None:
                        # Fix 1: ensure generation_config is not None
                        if getattr(inf_model, "generation_config", None) is None:
                            inf_model.generation_config = GenerationConfig()
                        # Fix 2: nuke the validation guard on the live instance
                        inf_model._validate_model_class = lambda: None
                        inf_model.__class__._validate_model_class = lambda self: None
                        inf_model.__class__._supports_generate = True
                    with _torch.inference_mode():
                        out = self._model.synthesize(
                            text=clean,
                            speaker_wav=speaker_wav,
                            language=language,
                            **synth_kwargs,
                        )
                    return self._postprocess(np.array(out["wav"], dtype=np.float32))
                except Exception as e_retry:
                    log.error("[TTS ERROR] Retry after runtime fix failed: %s", e_retry)
                return None

            # CUDA crash -> retry on CPU
            if self._device == "cuda" and ("no kernel" in err or "cuda" in err):
                print("[TTS] CUDA error during synthesis — switching to CPU and retrying")
                self._device = "cpu"
                try:
                    self._model.to("cpu")
                    self._model.eval()
                    with _torch.inference_mode():
                        out = self._model.synthesize(
                            text=clean,
                            speaker_wav=speaker_wav, language=language,
                            **synth_kwargs,
                        )
                    return self._postprocess(np.array(out["wav"], dtype=np.float32))
                except Exception as e2:
                    log.error("[TTS ERROR] CPU retry also failed: %s", e2)

            # Index / tokenizer error → retry with aggressive clean
            if "index out of range" in err:
                simple = self._clean_text(text, aggressive=True)
                try:
                    with _torch.inference_mode():
                        out = self._model.synthesize(
                            text=simple,
                            speaker_wav=speaker_wav, language=language,
                            **synth_kwargs,
                        )
                    return self._postprocess(np.array(out["wav"], dtype=np.float32))
                except Exception as e3:
                    log.error("[TTS ERROR] Simplified retry failed: %s", e3)

            return None

    def _postprocess(self, audio: np.ndarray) -> np.ndarray:
        """Normalise, clip, and ensure contiguous float32."""
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        audio = np.nan_to_num(audio, copy=False)
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak > 0:
            audio = (audio / peak) * 0.92
        audio = np.clip(audio, -0.98, 0.98)
        return np.ascontiguousarray(audio, dtype=np.float32)

    def _play(self, audio: np.ndarray):
        """Play float32 audio via sounddevice with optional resampling."""
        if _sd is None:
            log.error("[TTS] sounddevice not available — cannot play audio")
            return
        model_sr = self._settings.get("sample_rate", 24000)
        out_sr   = self._device_samplerate
        if out_sr != model_sr and _resample_poly is not None:
            audio = _resample_poly(audio, out_sr, model_sr).astype(np.float32)
        _sd.play(audio, samplerate=out_sr, blocking=True)

    # ------------------------------------------------------------------ #
    def _clean_text(self, text: str, aggressive: bool = False) -> str:
        import re
        t = " ".join((text or "").strip().split())
        if not aggressive:
            return t
        t = re.sub(r"[^a-zA-Z0-9 .,!?'-]", " ", t)
        t = " ".join(t.split())
        return t[:120] or "Done."

    # ------------------------------------------------------------------ #
    #  Speaking state management
    # ------------------------------------------------------------------ #
    def _set_speaking(self, state: bool):
        self._is_speaking = state
        for cb in self._speaking_callbacks:
            try:
                cb(state)
            except Exception:
                pass

    def register_speaking_callback(self, cb):
        """Register a callback(bool) that fires when speech starts/stops."""
        self._speaking_callbacks.append(cb)

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #
    def speak(self, text: str):
        """
        Queue `text` for TTS playback (non-blocking).
        Returns immediately; playback happens on the worker thread.
        """
        if text and text.strip():
            self._speech_queue.put(text)

    def speak_blocking(self, text: str):
        """
        Synthesise and play `text` synchronously (blocks caller).
        Useful for startup messages in __main__ threads.
        """
        if text and text.strip():
            self._synthesise_and_play(text)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking


# ---------------------------------------------------------------------------
# Module-level singleton accessor
# ---------------------------------------------------------------------------
_manager_instance: Optional[_TTSManager] = None
_manager_init_lock = threading.Lock()


def init_tts(settings: dict) -> _TTSManager:
    """
    Initialise the global TTS manager with the given settings dict.
    Must be called once before speak() is used.
    """
    global _manager_instance
    with _manager_init_lock:
        if _manager_instance is None:
            _manager_instance = _TTSManager(settings)
    return _manager_instance


def get_tts() -> Optional[_TTSManager]:
    """Return the already-initialised TTS manager, or None if not yet initialised."""
    return _manager_instance


def speak(text: str):
    """
    Module-level speak() helper.
    Queues text for non-blocking XTTS playback.
    If TTS is not loaded, logs and silently continues.
    """
    mgr = _manager_instance
    if mgr is None:
        print(f"[TTS] (not loaded) {text}")
        return
    try:
        mgr.speak(text)
    except Exception as e:
        log.error("[TTS] speak() error: %s", e)


def speak_blocking(text: str):
    """Synchronous wrapper — blocks until audio finishes."""
    mgr = _manager_instance
    if mgr is None:
        print(f"[TTS] (not loaded) {text}")
        return
    try:
        mgr.speak_blocking(text)
    except Exception as e:
        log.error("[TTS] speak_blocking() error: %s", e)
