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
        # Keep previous hardcoded default as safety.
        return r"K:\PROJECTS\Phone agent\Jarvis_TTS\output\xtts_run_20260507_224555\run-May-07-2026_10+46PM-0000000"
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]

class Config:
    # TTS
    XTTS_MODEL_DIR = r"K:\PROJECTS\Phone agent\Jarvis_TTS\output\xtts_run_20260507_224555\run-May-07-2026_10+46PM-0000000"
    if not os.path.exists(XTTS_MODEL_DIR):
        XTTS_MODEL_DIR = _detect_xtts_model_dir()
    XTTS_CHECKPOINT = _first_existing(
        [
            os.path.join(XTTS_MODEL_DIR, "checkpoint_1000.pth"),
            _latest_checkpoint(XTTS_MODEL_DIR),
            os.path.join(XTTS_MODEL_DIR, "model.pth"),
            os.path.join(XTTS_MODEL_DIR, "best_model.pth"),
        ]
    )
    XTTS_CONFIG = os.path.join(XTTS_MODEL_DIR, "config.json")
    XTTS_VOCAB = os.path.join(XTTS_MODEL_DIR, "vocab.json")
    XTTS_SPEAKERS = _first_existing(
        [
            os.path.join(XTTS_MODEL_DIR, "speakers_xtts.pth"),
            os.path.join(XTTS_MODEL_DIR, "speakers.pth"),
        ]
    )
    
    # We need a reference speaker wav for XTTS. Let's assume there's one in the dataset.
    XTTS_SPEAKER_WAV = _first_existing(
        [
            os.path.join(XTTS_MODEL_DIR, "reference.wav"),
            os.path.join(XTTS_MODEL_DIR, "speaker.wav"),
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
    # RTX 5050 (sm_120) is currently unsupported by your PyTorch build for XTTS.
    # Keep XTTS on CPU for stable voice replies.
    XTTS_FORCE_CPU = True
    XTTS_ENABLE_TEXT_SPLITTING = True

    
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
