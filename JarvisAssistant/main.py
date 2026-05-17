import os
import sys
import site
import contextlib
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Add CUDA library paths to PATH so CTranslate2 can find cudnn DLLs
for _p in site.getsitepackages():
    for _sub in ("nvidia/cudnn/bin", "nvidia/cublas/bin"):
        _full = os.path.join(_p, *_sub.split("/"))
        if os.path.exists(_full) and _full not in os.environ["PATH"]:
            os.environ["PATH"] = _full + os.pathsep + os.environ["PATH"]

import asyncio
from jarvis_core.event_bus import bus
from jarvis_voice.wake_word import JarvisWakeWord
from jarvis_voice.microphone import CommandListener
from jarvis_voice.stt import JarvisSTT
from jarvis_voice.tts import JarvisTTS
from jarvis_agents.intent_parser import IntentParser
from jarvis_network.router import DeviceRouter


class JarvisApp:
    def __init__(self):
        print("Initializing JARVIS modules...")
        self.tts = JarvisTTS()
        self.stt = JarvisSTT()
        self.parser = IntentParser()
        self.router = DeviceRouter()
        self.mic = CommandListener()
        self.wake_word = JarvisWakeWord()

        # Wire TTS speaking state into the wake-word listener's mic mute
        self.tts.set_speaking_callback(self.wake_word.set_speaking)

        self.is_processing = False
        self.command_queue = asyncio.Queue(maxsize=1)

        # Register event handlers
        bus.subscribe("WakeWordDetected", self.on_wake_word)

    async def on_wake_word(self, data=None):
        if self.is_processing or self.command_queue.full():
            return
        await self.command_queue.put(True)

    async def _command_worker(self):
        while True:
            await self.command_queue.get()
            self.is_processing = True
            try:
                # Acknowledge with the correct phrase.
                await asyncio.to_thread(self.tts.speak, "Yes Sir ..?")

                # Record + STT off the event loop.
                audio_data = await asyncio.to_thread(self.mic.record_command)
                print("Transcribing...")
                text = await asyncio.to_thread(self.stt.transcribe, audio_data)
                print(f"You said: {text!r}")

                if text:
                    intent = await asyncio.to_thread(self.parser.parse_intent, text)
                    print(f"Parsed Intent: {intent}")
                    await asyncio.to_thread(self.router.route_intent, intent)
                    response_text = self._build_voice_response(intent)
                    await asyncio.to_thread(self.tts.speak, response_text)
                else:
                    await asyncio.to_thread(self.tts.speak, "I didn't catch that. Please try again.")
            except Exception as e:
                print(f"[ERROR] command worker: {e}")
            finally:
                self.is_processing = False
                if self.wake_word._speaking:
                    self.wake_word.set_speaking(False)
                self.command_queue.task_done()

    def _build_voice_response(self, intent: dict) -> str:
        params = intent.get("parameters", {}) or {}
        explicit = params.get("response_text")
        if explicit:
            return explicit

        action = (intent.get("action") or "").lower()
        if action == "open_app":
            app_name = params.get("app_name", "the app")
            return f"Opening {app_name}."
        if action == "search_web":
            query = params.get("query", "that")
            return f"Searching the web for {query}."
        if action == "send_message":
            contact = params.get("contact_name", "the contact")
            return f"Sending message to {contact}."
        if action == "system_control":
            operation = (params.get("operation") or "that action").replace("_", " ")
            return f"Executing {operation}."
        if action == "chat":
            return params.get("text", "Done.")
        return "Done."

    def start(self):
        print("JARVIS System Online.")
        self.tts.speak("Yes Sir ..?")

        async def main_loop():
            worker = asyncio.create_task(self._command_worker())
            wake_listener = asyncio.create_task(self.wake_word.listen_for_wake_word())
            try:
                await wake_listener
            finally:
                worker.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await worker

        asyncio.run(main_loop())


if __name__ == "__main__":
    app = JarvisApp()
    try:
        app.start()
    except KeyboardInterrupt:
        print("\nShutting down JARVIS...")
        app.wake_word.stop()
        app.mic.terminate()
