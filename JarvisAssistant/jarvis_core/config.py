import os
from glob import glob
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", "voice_agent_hub", ".env"))


def _first_existing(paths):
    for path in paths:
        if path and os.path.exists(path):
            return path
    return None


def _latest_checkpoint(model_dir: str) -> str:
    checkpoints = sorted(glob(os.path.join(model_dir, "checkpoint*.pth")))
    if not checkpoints:
        return ""
    checkpoints.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return checkpoints[0]


def _detect_xtts_model_dir() -> str:
    """
    Detect the newest trained XTTS output directory that contains a config and checkpoint.
    Falls back to the most recently modified run directory.
    """
    base = r"K:\PROJECTS\Phone agent\Jarvis_TTS\output"
    candidates = []
    for run_dir in glob(os.path.join(base, "xtts_run_*")):
        for sub_dir in glob(os.path.join(run_dir, "run-*")):
            has_cfg = os.path.exists(os.path.join(sub_dir, "config.json"))
            has_ckpt = bool(glob(os.path.join(sub_dir, "checkpoint*.pth"))) or os.path.exists(
                os.path.join(sub_dir, "model.pth")
            )
            if has_cfg and has_ckpt:
                candidates.append(sub_dir)
    if not candidates:
        # Hardcoded fallback — pinned run
        return r"K:\PROJECTS\Phone agent\Jarvis_TTS\output\xtts_run_20260511_175657\run-May-11-2026_05+57PM-0000000"
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]

class Config:
    # ---------------------------------------------------------------------------
    # TTS — pinned to the specified run and checkpoint
    # ---------------------------------------------------------------------------
    XTTS_MODEL_DIR = r"K:\PROJECTS\Phone agent\Jarvis_TTS\output\xtts_run_20260511_175657\run-May-11-2026_05+57PM-0000000"
    # Fall back to auto-detection only if the pinned dir doesn't exist
    if not os.path.isdir(XTTS_MODEL_DIR):
        XTTS_MODEL_DIR = _detect_xtts_model_dir()

    XTTS_CHECKPOINT = _first_existing(
        [
            # Pinned checkpoint first
            os.path.join(XTTS_MODEL_DIR, "checkpoint_4284.pth"),
            os.path.join(XTTS_MODEL_DIR, "checkpoint_4500.pth"),
            os.path.join(XTTS_MODEL_DIR, "checkpoint_1000.pth"),
            os.path.join(XTTS_MODEL_DIR, "model.pth"),
            os.path.join(XTTS_MODEL_DIR, "best_model.pth"),
        ]
    )
    XTTS_CONFIG = os.path.join(XTTS_MODEL_DIR, "config.json")

    # vocab.json lives in the AppData TTS cache (shared base model)
    XTTS_VOCAB = _first_existing(
        [
            os.path.join(XTTS_MODEL_DIR, "vocab.json"),
            r"C:\Users\Kasinathan P S\AppData\Local\tts\tts_models--multilingual--multi-dataset--xtts_v2\vocab.json",
        ]
    )

    XTTS_SPEAKERS = _first_existing(
        [
            os.path.join(XTTS_MODEL_DIR, "speakers_xtts.pth"),
            os.path.join(XTTS_MODEL_DIR, "speakers.pth"),
        ]
    )

    # Reference speaker wav — pinned to the matching checkpoint-4284 recording
    XTTS_SPEAKER_WAV = _first_existing(
        [
            r"K:\PROJECTS\Phone agent\Jarvis_TTS\4284.wav",
            os.path.join(XTTS_MODEL_DIR, "reference.wav"),
            os.path.join(XTTS_MODEL_DIR, "speaker.wav"),
            r"K:\PROJECTS\Phone agent\Jarvis_TTS\dataset\wavs\caged_intro_2.wav",
            r"K:\PROJECTS\Phone agent\Jarvis_TTS\dataset\wavs\caged_welcome.wav",
        ]
    )

    XTTS_LANGUAGE = "en"
    XTTS_INTERNAL_SAMPLE_RATE = 24000
    XTTS_TARGET_PEAK = 0.92
    XTTS_USE_FAST_INFERENCE = True
    XTTS_GPT_COND_LEN = 1
    XTTS_DECODER_ITERATIONS = 12
    XTTS_TOP_K = 20
    XTTS_TOP_P = 0.75
    XTTS_TEMPERATURE = 0.45
    ALLOW_SYSTEM_TTS_FALLBACK = False
    ALLOW_SAPI_EMERGENCY_FALLBACK = False
    # RTX 5050 (sm_120) with current PyTorch build — keep XTTS on CPU for stability.
    # Set XTTS_FORCE_CPU = False once you upgrade to a sm_120-compatible torch build.
    XTTS_FORCE_CPU = True
    XTTS_ENABLE_TEXT_SPLITTING = True

    # ------------------------------------------------------------------
    # Convenience: return a settings dict for audio/tts_manager.py
    # ------------------------------------------------------------------
    @classmethod
    def get_tts_settings(cls) -> dict:
        return {
            "model_dir":          cls.XTTS_MODEL_DIR,
            "config_path":        cls.XTTS_CONFIG,
            "checkpoint_path":    cls.XTTS_CHECKPOINT,
            "vocab_path":         cls.XTTS_VOCAB or "",
            "speaker_wav":        cls.XTTS_SPEAKER_WAV or "",
            "language":           cls.XTTS_LANGUAGE,
            "sample_rate":        cls.XTTS_INTERNAL_SAMPLE_RATE,
            "use_gpu":            not cls.XTTS_FORCE_CPU,
            "use_fast_inference": cls.XTTS_USE_FAST_INFERENCE,
            "gpt_cond_len":       cls.XTTS_GPT_COND_LEN,
            "decoder_iterations": cls.XTTS_DECODER_ITERATIONS,
            "top_k":              cls.XTTS_TOP_K,
            "top_p":              cls.XTTS_TOP_P,
            "temperature":        cls.XTTS_TEMPERATURE,
        }

    
    # STT — use GPU if CTranslate2 CUDA is available
    WHISPER_MODEL = "base.en"
    @staticmethod
    def get_whisper_device():
        try:
            import ctranslate2
            if ctranslate2.get_supported_compute_types("cuda"):
                return "cuda", "float16"
        except Exception:
            pass
        return "cpu", "int8"

    # LLM
    OLLAMA_MODEL = "llama3"
    OLLAMA_URL = "http://localhost:11434/api/generate"

    # Android devices (read from .env)
    MOBILE_IP_PORT  = os.getenv("MOBILE_IP_PORT",  "192.168.1.7:5555")
    TABLET_IP_PORT  = os.getenv("TABLET_IP_PORT",  "192.168.1.3:5555")

    # Automation timing
    UI_ACTION_DELAY = 0.2
    WHATSAPP_SEARCH_DELAY = 0.9
    WHATSAPP_TYPE_DELAY = 0.01

config = Config()
