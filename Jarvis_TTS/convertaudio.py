from pydub import AudioSegment
import os

INPUT_FOLDER = r"K:\PROJECTS\Jarvis TTS\dataset\wavs"

for filename in os.listdir(INPUT_FOLDER):

    if filename.lower().endswith(".wav"):

        file_path = os.path.join(INPUT_FOLDER, filename)

        print(f"Converting: {filename}")

        audio = AudioSegment.from_wav(file_path)

        # Convert to mono
        audio = audio.set_channels(1)

        # Convert to 24kHz
        audio = audio.set_frame_rate(24000)

        # Export as 16-bit PCM WAV
        audio.export(
            file_path,
            format="wav",
            codec="pcm_s16le"
        )

print("All files converted successfully.")