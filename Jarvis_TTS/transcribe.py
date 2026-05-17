import whisper
import os

model = whisper.load_model("medium")

audio_folder = "wavs"

with open("metadata.csv", "w", encoding="utf-8") as f:
    for file in os.listdir(audio_folder):
        if file.endswith(".wav"):
            path = os.path.join(audio_folder, file)

            result = model.transcribe(path)

            text = result["text"].strip()

            name = file.replace(".wav", "")

            line = f"{name}|{text}\n"

            f.write(line)

            print(line)