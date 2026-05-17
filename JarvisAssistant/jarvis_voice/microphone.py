import pyaudio
import numpy as np
import time


class CommandListener:
    """
    Records a command using Voice Activity Detection (VAD).
    - Waits for the user to start speaking (up to `pre_speech_timeout` seconds).
    - Stops recording automatically when the user goes silent for `silence_timeout` seconds.
    - Hard cap of `max_duration` seconds to prevent runaway recording.
    """

    def __init__(self, rate=16000, chunk=1024):
        self.rate = rate
        self.chunk = chunk
        self.format = pyaudio.paInt16
        self.channels = 1
        self.audio = pyaudio.PyAudio()

        # VAD thresholds (tuned for fast, precise capture)
        self._silence_rms_threshold = 200   # RMS below this = silence (lower = catches soft speech)
        self._silence_timeout = 0.9         # seconds of silence before stopping
        self._pre_speech_timeout = 4.0      # max wait for speech to start
        self._max_duration = 8.0            # hard cap on total recording

    def _rms(self, data: bytes) -> float:
        samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        return float(np.sqrt(np.mean(samples ** 2))) if len(samples) > 0 else 0.0

    def record_command(self) -> np.ndarray:
        """Smart VAD recording. Returns float32 numpy array normalized to [-1, 1]."""
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
        )

        print("Listening for command...")
        frames = []
        speech_started = False
        silence_start = None
        recording_start = time.time()

        try:
            while True:
                elapsed = time.time() - recording_start
                data = stream.read(self.chunk, exception_on_overflow=False)
                rms = self._rms(data)

                if not speech_started:
                    if rms > self._silence_rms_threshold:
                        print("Recording...")
                        speech_started = True
                        frames.append(data)
                    elif elapsed > self._pre_speech_timeout:
                        print("No speech detected.")
                        break
                else:
                    frames.append(data)
                    if rms < self._silence_rms_threshold:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > self._silence_timeout:
                            print("Recording stopped (silence).")
                            break
                    else:
                        silence_start = None  # reset silence timer when speech resumes

                if elapsed > self._max_duration:
                    print("Recording stopped (max duration reached).")
                    break
        finally:
            stream.stop_stream()
            stream.close()

        if not frames:
            return np.zeros(self.rate, dtype=np.float32)

        audio_data = b"".join(frames)
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        return audio_np

    def terminate(self):
        self.audio.terminate()
