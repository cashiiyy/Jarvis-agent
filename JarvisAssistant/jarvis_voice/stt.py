from faster_whisper import WhisperModel
from jarvis_core.config import config
import numpy as np


class JarvisSTT:
    def __init__(self):
        device, compute_type = config.get_whisper_device()
        print(f"Loading Whisper model: {config.WHISPER_MODEL} [{device.upper()} / {compute_type}]")
        self.model = WhisperModel(
            config.WHISPER_MODEL,
            device=device,
            compute_type=compute_type,
            num_workers=2,
        )

    def transcribe(self, audio_data: np.ndarray) -> str:
        """Transcribe a float32 numpy array (values in [-1, 1]) to text."""
        if audio_data is None or len(audio_data) < self.model.feature_extractor.hop_length:
            return ""
        segments, _ = self.model.transcribe(
            audio_data,
            beam_size=3,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400),
        )
        text = " ".join(seg.text.strip() for seg in segments)
        return text.strip()


if __name__ == "__main__":
    stt = JarvisSTT()
    print("STT module loaded.")
