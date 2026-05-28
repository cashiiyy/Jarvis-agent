import torch
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import soundfile as sf
import librosa
import os

# ADD SAFE GLOBALS FOR PYTORCH 2.6+
from TTS.tts.models.xtts import XttsArgs, XttsAudioConfig
from TTS.config.shared_configs import BaseDatasetConfig
torch.serialization.add_safe_globals([
    XttsConfig,
    XttsAudioConfig,
    XttsArgs,
    BaseDatasetConfig,
])

def custom_load_audio(audiopath, sampling_rate):
    wav, sr_orig = sf.read(audiopath, dtype="float32")
    if wav.ndim > 1:
        wav = wav.mean(axis=1) # stereo to mono
    if sr_orig != sampling_rate:
        wav = librosa.resample(wav, orig_sr=sr_orig, target_sr=sampling_rate)
    wav = wav.clip(-1.0, 1.0)
    return torch.tensor(wav).unsqueeze(0).float()

import TTS.tts.models.xtts
TTS.tts.models.xtts.load_audio = custom_load_audio

MODEL_CHECKPOINT = r"K:\PROJECTS\Phone agent\Jarvis_TTS\output\xtts_run_20260511_175657\run-May-11-2026_05+57PM-0000000\checkpoint_4284.pth"
CONFIG_PATH = r"K:\PROJECTS\Phone agent\Jarvis_TTS\output\xtts_run_20260511_175657\run-May-11-2026_05+57PM-0000000\config.json"
SPEAKER_WAV = r"K:\PROJECTS\Phone agent\Jarvis_TTS\dataset\wavs\caged_intro_2.wav"
OUTPUT_PATH = r"K:\PROJECTS\Phone agent\Jarvis_TTS\result.wav"
VOCAB_PATH = r"C:\Users\Kasinathan P S\AppData\Local\tts\tts_models--multilingual--multi-dataset--xtts_v2\vocab.json"
SPEAKER_FILE_PATH = None  # No speakers file in the new run folder

# Load config
config = XttsConfig()
config.load_json(CONFIG_PATH)

# Initialize model
model = Xtts.init_from_config(config)

# Load checkpoint
model.load_checkpoint(
    config,
    checkpoint_dir=r"K:\PROJECTS\Phone agent\Jarvis_TTS\output\xtts_run_20260511_175657\run-May-11-2026_05+57PM-0000000",
    checkpoint_path=MODEL_CHECKPOINT,
    vocab_path=VOCAB_PATH,
    speaker_file_path=SPEAKER_FILE_PATH,
    eval=True
)

# Move to GPU if available
if torch.cuda.is_available():
    model.cuda()

# Generate speech
text_to_speak = (
    "All Systems online, SIR ."
    "All neural matrices fully synchronized and Initial audio calibration is now completed."
    "Re-routing computational power to core functions."
    "Initialising systems."
    "Hi , I am Jarvis.Your personal assistant."
    "Shall we proceed with the next experiment?"
    )

outputs = model.synthesize(
    text=text_to_speak,
    config=config,
    speaker_wav=SPEAKER_WAV,
    language="en",
    enable_text_splitting=True, # Splitting requires proper spaces after punctuation to work correctly
    # Note: The 'speed' parameter uses latent interpolation which severely degrades quality and causes a robotic, low-pitch voice.
    # To maintain maximum human-like quality, keep speed at 1.0 (default). If you need slower speech, use a slower reference WAV.
)

# Save audio
sf.write(OUTPUT_PATH, outputs["wav"], 24000)
print(f"DONE. Audio saved to {OUTPUT_PATH}")