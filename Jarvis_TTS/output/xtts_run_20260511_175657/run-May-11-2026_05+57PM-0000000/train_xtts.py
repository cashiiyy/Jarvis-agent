import os
import torch
import dataclasses
from datetime import datetime
from trainer import Trainer, TrainerArgs

from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsArgs, XttsAudioConfig
from TTS.tts.layers.xtts.trainer.gpt_trainer import GPTTrainer, GPTTrainerConfig, GPTArgs
import soundfile as sf
import librosa

# ── GPU check ────────────────────────────────────────────────────────────────
if torch.cuda.is_available():
    GPU_NAME = torch.cuda.get_device_name(0)
    GPU_VRAM = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1)
    print(f"[GPU] Using: {GPU_NAME}  |  VRAM: {GPU_VRAM} GB")
else:
    print("[WARNING] CUDA not available — falling back to CPU")

def custom_load_audio(audiopath, sampling_rate):
    wav, sr_orig = sf.read(audiopath, dtype="float32")
    if wav.ndim > 1:
        wav = wav.mean(axis=1) # stereo to mono
    if sr_orig != sampling_rate:
        wav = librosa.resample(wav, orig_sr=sr_orig, target_sr=sampling_rate)
    wav = wav.clip(-1.0, 1.0)
    return torch.tensor(wav).unsqueeze(0).float()

import TTS.tts.models.xtts
import TTS.tts.layers.xtts.trainer.dataset
TTS.tts.models.xtts.load_audio = custom_load_audio
TTS.tts.layers.xtts.trainer.dataset.load_audio = custom_load_audio

from TTS.tts.layers.xtts.trainer.gpt_trainer import XttsAudioConfig as GPTAudioConfig
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.datasets import load_tts_samples

# ADD SAFE GLOBALS FOR PYTORCH 2.6+
torch.serialization.add_safe_globals([
    XttsConfig,
    XttsAudioConfig,
    XttsArgs,
    BaseDatasetConfig,
    GPTTrainerConfig,
    GPTArgs,
    GPTAudioConfig
])

# Monkey-patch XttsArgs and GPTArgs to avoid AttributeErrors in newer TTS versions
for cls in [XttsArgs, GPTArgs]:
    if not hasattr(cls, "debug_loading_failures"):
        cls.debug_loading_failures = False
    if not hasattr(cls, "max_conditioning_length"):
        cls.max_conditioning_length = 132300  # Default for XTTS
    if not hasattr(cls, "min_conditioning_length"):
        cls.min_conditioning_length = 6615  # Default for XTTS
    if not hasattr(cls, "max_wav_length"):
        cls.max_wav_length = 250000 
    if not hasattr(cls, "max_text_length"):
        cls.max_text_length = 400
    if not hasattr(cls, "gpt_max_audio_tokens"):
        cls.gpt_max_audio_tokens = 605
    if not hasattr(cls, "gpt_max_text_tokens"):
        cls.gpt_max_text_tokens = 402
    if not hasattr(cls, "gpt_max_prompt_tokens"):
        cls.gpt_max_prompt_tokens = 70

# Monkey-patch XttsAudioConfig
if not hasattr(XttsAudioConfig, "dvae_sample_rate"):
    XttsAudioConfig.dvae_sample_rate = 22050
if not hasattr(GPTAudioConfig, "dvae_sample_rate"):
    GPTAudioConfig.dvae_sample_rate = 22050

def main():
    RUN_NAME = datetime.now().strftime("%Y%m%d_%H%M%S")
    DATASET_PATH = "dataset"
    XTTS_CHECKPOINT = (
        "C:/Users/Kasinathan P S/AppData/Local/tts/"
        "tts_models--multilingual--multi-dataset--xtts_v2"
    )
    OUTPUT_PATH = f"./output/xtts_run_{RUN_NAME}"

    dataset_config = BaseDatasetConfig(
        formatter="ljspeech",
        dataset_name="jarvis",
        path=DATASET_PATH,
        meta_file_train="metadata.csv",
        language="en",
    )

    config = GPTTrainerConfig()
    config.load_json(os.path.join(XTTS_CHECKPOINT, "config.json"))

    # ── GPU vs CPU settings ──────────────────────────────────────────────────
    USE_GPU = torch.cuda.is_available()
    config.output_path = OUTPUT_PATH
    config.batch_size      = 2 if USE_GPU else 1       # batch 2 is safe for 8GB VRAM in fp32
    config.grad_accum_steps = 8 if USE_GPU else 16     # effective batch = 16 on GPU
    config.num_loader_workers = 4 if USE_GPU else 0    # parallel data loading on GPU
    config.run_eval        = False
    config.eval_split_size = 0.01
    config.epochs          = 30                        # set to 30 epochs total
    config.mixed_precision = False                     # fp32 — fp16 causes NaN with XTTS cross-entropy
    config.optimizer       = "AdamW"
    config.optimizer_params = {"weight_decay": 1e-2, "betas": [0.9, 0.96], "eps": 1e-8}
    config.lr_scheduler    = "MultiStepLR"
    config.lr_scheduler_params = {"milestones": [50000 * 18, 150000 * 18, 300000 * 18], "gamma": 0.5, "last_epoch": -1}
    config.lr              = 5e-6
    config.print_step      = 50
    config.save_step       = 500                       # save checkpoint every 500 steps

    # XTTS requires tokenizer and dvae checkpoints
    # Convert XttsArgs to GPTArgs
    model_args_dict = dataclasses.asdict(config.model_args)
    config.model_args = GPTArgs(**model_args_dict)
    
    config.model_args.xtts_checkpoint = os.path.join(XTTS_CHECKPOINT, "model.pth")
    config.model_args.tokenizer_file = os.path.join(XTTS_CHECKPOINT, "vocab.json")
    config.model_args.dvae_checkpoint = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dvae.pth")
    config.model_args.mel_norm_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mel_stats.pth")
    config.model_args.max_wav_length = 153600  # Strictly enforce max length to prevent CUDA out of bounds
    config.model_args.max_text_length = 400


    # Convert audio config
    audio_config_dict = dataclasses.asdict(config.audio)
    config.audio = GPTAudioConfig(**audio_config_dict)

    train_samples, eval_samples = load_tts_samples(dataset_config, eval_split=True)
    
    # Pre-filter samples to avoid XTTSDataset RecursionError and Out-of-Bounds
    def is_valid_sample(s):
        try:
            text = s.get("text", "").strip()
            if len(text) < 2:  # skip empty/near-empty transcripts (e.g. caged_power_down)
                return False
            if len(text) > 250:
                return False
            wav, sr = sf.read(s["audio_file"])
            if wav.ndim > 1:
                wav = wav.mean(axis=1)
            if len(wav) > 153600 or len(wav) < 2000:
                return False
            return True
        except Exception as e:
            print(f"  Skipping {s.get('audio_file','?')}: {e}")
            return False

    print("Filtering samples to fit model context window...")
    train_samples = [s for s in train_samples if is_valid_sample(s)]
    eval_samples = [s for s in eval_samples if is_valid_sample(s)]
    print(f"Loaded {len(train_samples)} training samples and {len(eval_samples)} eval samples")
    
    model = GPTTrainer.init_from_config(config)

    trainer = Trainer(
        TrainerArgs(
            restore_path=None,
            continue_path="k:/PROJECTS/Phone agent/Jarvis_TTS/output/xtts_run_20260511_175657/run-May-11-2026_05+57PM-0000000",
            skip_train_epoch=False, 
            start_with_eval=False, 
            grad_accum_steps=1
        ),
        config,
        output_path=OUTPUT_PATH,
        model=model,
        train_samples=train_samples,
        eval_samples=eval_samples,
    )

    # Removed manual override to let the trainer show the real progress (approx 24 epochs)
    # trainer.epochs_done = 5 

    try:
        trainer.fit()
    except Exception as e:
        print("TRAINING ERROR:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()