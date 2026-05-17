from TTS.api import TTS

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

tts.tts_to_file(
    text="Good evening Shanthi.How are you ? What are we doing today ?",
    speaker_wav="K:/PROJECTS/Jarvis TTS/dataset/wavs/caged_intro_2.wav",
    language="en",
    file_path="output.wav"
)