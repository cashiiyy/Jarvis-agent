import sys
import traceback
sys.path.insert(0, '.')

try:
    from jarvis_voice.tts import JarvisTTS
    tts = JarvisTTS()
    tts.speak("Systems are online and ready, sir.")
    print("TTS SUCCESS")
except Exception:
    traceback.print_exc()
