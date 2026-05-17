import os
import re
import threading
import time
import logging
import torch
import numpy as np
import sounddevice as sd
try:
    import pyttsx3
except Exception:
    pyttsx3 = None
from scipy.signal import resample_poly

from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

from jarvis_core.config import config


# ---------------------------------------------------------------------------
# Fast system TTS (pyttsx3 / Windows SAPI) — used for short phrases or fallback
# ---------------------------------------------------------------------------
def _make_sapi_engine():
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        for v in voices:
            if "david" in v.name.lower() or "mark" in v.name.lower():
                engine.setProperty("voice", v.id)
                break
        engine.setProperty("rate", 190)
        engine.setProperty("volume", 0.9)
        return engine
    except Exception:
        return None


class JarvisTTS:
    def __init__(self):
        self.logger = logging.getLogger("jarvis.tts")
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")
        self.device = "cpu" if config.XTTS_FORCE_CPU else ("cuda" if torch.cuda.is_available() else "cpu")
        self.sample_rate = config.XTTS_INTERNAL_SAMPLE_RATE
        self.speaker_wav = config.XTTS_SPEAKER_WAV
        self.model = None
        self.gpt_cond_latent = None
        self.speaker_embedding = None
        self._speaking_callback = None
        self._sapi = _make_sapi_engine()
        self._playback_lock = threading.Lock()
        self._device_samplerate = self._resolve_device_sample_rate()
        self._validate_model_assets()
        self._load_model()

    def set_speaking_callback(self, cb):
        self._speaking_callback = cb

    def _load_model(self):
        self.logger.info("Loading XTTS model: %s", config.XTTS_CHECKPOINT)
        xtts_config = XttsConfig()
        xtts_config.load_json(config.XTTS_CONFIG)
        self.xtts_config = xtts_config
        self.model = Xtts.init_from_config(xtts_config)
        try:
            self.model.load_checkpoint(
                xtts_config,
                checkpoint_dir=config.XTTS_MODEL_DIR,
                checkpoint_path=config.XTTS_CHECKPOINT,
                vocab_path=config.XTTS_VOCAB if config.XTTS_VOCAB and os.path.exists(config.XTTS_VOCAB) else None,
                eval=True,
                strict=False,
            )
        except Exception as e:
            self.logger.warning("load_checkpoint() failed, using compatibility loader: %s", e)
            self._load_checkpoint_compat(config.XTTS_CHECKPOINT)
        self._setup_model_with_fallback()
        self.logger.info("Custom XTTS voice ready.")

    def _load_checkpoint_compat(self, checkpoint_path: str):
        ckpt = torch.load(checkpoint_path, map_location="cpu")
        state_dict = ckpt.get("model", ckpt)
        remapped = {}
        for k, v in state_dict.items():
            nk = k
            if nk.startswith("xtts."):
                nk = nk[5:]
            # Some checkpoints contain gpt.gpt_inference.* while runtime expects gpt.gpt.*
            nk = nk.replace("gpt.gpt_inference.", "gpt.gpt.")
            remapped[nk] = v
        missing, unexpected = self.model.load_state_dict(remapped, strict=False)
        self.logger.info(
            "Compatibility load done (missing=%d, unexpected=%d)",
            len(missing),
            len(unexpected),
        )

    def speak(self, text: str, force_sapi=False):
        if not text or not text.strip():
            return
        self.logger.info("Speak: %s", text)

        if self._speaking_callback:
            self._speaking_callback(True)
        
        try:
            if force_sapi and self._sapi:
                self._speak_sapi(text)
            else:
                self._speak_xtts(text)
        finally:
            if self._speaking_callback:
                self._speaking_callback(False)

    def _speak_sapi(self, text: str):
        if self._sapi:
            self._sapi.say(text)
            self._sapi.runAndWait()

    def _speak_xtts(self, text: str):
        try:
            t0 = time.perf_counter()
            clean_text = self._clean_text(text)
            synth_kwargs = {}
            if config.XTTS_USE_FAST_INFERENCE:
                synth_kwargs = {
                    "gpt_cond_len": config.XTTS_GPT_COND_LEN,
                    "decoder_iterations": config.XTTS_DECODER_ITERATIONS,
                    "top_k": config.XTTS_TOP_K,
                    "top_p": config.XTTS_TOP_P,
                    "temperature": config.XTTS_TEMPERATURE,
                }
            with torch.inference_mode():
                out = self.model.synthesize(
                    text=clean_text,
                    config=self.xtts_config,
                    speaker_wav=self.speaker_wav,
                    language=config.XTTS_LANGUAGE,
                    **synth_kwargs,
                )
            self.logger.info("Inference done in %.0f ms", (time.perf_counter() - t0) * 1000.0)
            audio = self._postprocess_audio(np.array(out["wav"], dtype=np.float32))
            with self._playback_lock:
                t1 = time.perf_counter()
                self._play_audio(audio)
                self.logger.info("Playback done in %.0f ms", (time.perf_counter() - t1) * 1000.0)
        except Exception as e:
            error_text = str(e).lower()
            self.logger.error("XTTS Error: %s", e)
            # Runtime CUDA crashes can happen even after model init; switch to CPU and retry once.
            if self.device == "cuda" and ("no kernel image is available" in error_text or "cuda" in error_text):
                try:
                    self.logger.warning("Switching XTTS runtime to CPU and retrying speech.")
                    self.device = "cpu"
                    self.model.to("cpu")
                    self.model.eval()
                    with torch.inference_mode():
                        out = self.model.synthesize(
                            text=clean_text,
                            config=self.xtts_config,
                            speaker_wav=self.speaker_wav,
                            language=config.XTTS_LANGUAGE,
                            **synth_kwargs,
                        )
                    audio = self._postprocess_audio(np.array(out["wav"], dtype=np.float32))
                    with self._playback_lock:
                        self._play_audio(audio)
                    return
                except Exception as retry_error:
                    self.logger.error("XTTS CPU retry failed: %s", retry_error)

            # Tokenization edge-case guard for custom checkpoints/vocabs.
            if "index out of range" in error_text:
                try:
                    simple_text = self._clean_text(text, aggressive=True)
                    self.logger.warning("Retrying XTTS with simplified text: %s", simple_text)
                    with torch.inference_mode():
                        out = self.model.synthesize(
                            text=simple_text,
                            config=self.xtts_config,
                            speaker_wav=self.speaker_wav,
                            language=config.XTTS_LANGUAGE,
                            **synth_kwargs,
                        )
                    audio = self._postprocess_audio(np.array(out["wav"], dtype=np.float32))
                    with self._playback_lock:
                        self._play_audio(audio)
                    return
                except Exception as retry_error:
                    self.logger.error("XTTS simplified-text retry failed: %s", retry_error)

            # Optional emergency fallback to local SAPI if XTTS fails.
            if config.ALLOW_SAPI_EMERGENCY_FALLBACK and self._sapi:
                self.logger.warning("Using SAPI emergency fallback for this utterance.")
                self._speak_sapi(text)

    def _validate_model_assets(self):
        required = {
            "XTTS checkpoint": config.XTTS_CHECKPOINT,
            "XTTS config": config.XTTS_CONFIG,
            "XTTS speaker wav": config.XTTS_SPEAKER_WAV,
        }
        missing = [name for name, path in required.items() if not path or not os.path.exists(path)]
        if missing:
            raise FileNotFoundError(f"Missing required XTTS assets: {', '.join(missing)}")
        for optional_name, optional_path in [("XTTS vocab", config.XTTS_VOCAB), ("XTTS speakers", config.XTTS_SPEAKERS)]:
            if optional_path and not os.path.exists(optional_path):
                self.logger.warning("Optional file not found: %s -> %s", optional_name, optional_path)

    def _resolve_device_sample_rate(self) -> int:
        try:
            out_device = sd.query_devices(kind="output")
            sr = int(out_device.get("default_samplerate") or self.sample_rate)
            return sr if sr > 0 else self.sample_rate
        except Exception:
            return self.sample_rate

    def _postprocess_audio(self, audio: np.ndarray) -> np.ndarray:
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        audio = np.nan_to_num(audio, copy=False)
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak > 0:
            audio = (audio / peak) * config.XTTS_TARGET_PEAK
        # Keep dynamic range more natural to avoid metallic distortion.
        audio = np.clip(audio, -0.98, 0.98)
        return np.ascontiguousarray(audio, dtype=np.float32)

    def _play_audio(self, audio: np.ndarray):
        output_sr = self._device_samplerate
        if output_sr != self.sample_rate:
            audio = resample_poly(audio, output_sr, self.sample_rate).astype(np.float32, copy=False)
        sd.play(audio, samplerate=output_sr, blocking=True)

    def _clean_text(self, text: str, aggressive: bool = False) -> str:
        t = " ".join((text or "").strip().split())
        if not aggressive:
            return t
        t = re.sub(r"[^a-zA-Z0-9 .,!?'-]", " ", t)
        t = " ".join(t.split())
        if not t:
            return "Done."
        return t[:120]

    def _setup_model_with_fallback(self):
        if hasattr(self.model, "tokenizer") and not hasattr(self.model.tokenizer, "preprocess"):
            self.model.tokenizer.preprocess = True

        try:
            self.model.to(self.device)
            self.model.eval()
            self.logger.info("XTTS device: %s", self.device)
        except RuntimeError as e:
            error_text = str(e).lower()
            if self.device == "cuda" and ("no kernel image is available" in error_text or "cuda" in error_text):
                self.logger.warning("CUDA runtime unsupported on this GPU. Falling back to CPU.")
                self.device = "cpu"
                self.model.to(self.device)
                self.model.eval()
            else:
                raise

if __name__ == "__main__":
    tts = JarvisTTS()
    tts.speak("Hello Sir, what are we doing today?")
