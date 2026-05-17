import os
import subprocess
import time
import urllib.parse
import webbrowser
import pyautogui
import pyperclip

from jarvis_core.config import config

class WindowsController:
    def __init__(self):
        pyautogui.PAUSE = config.UI_ACTION_DELAY
        pyautogui.FAILSAFE = True

    def open_app(self, app_name: str):
        app_name = app_name.lower()
        print(f"WindowsController: Opening {app_name}")
        # Press win key, type app name, press enter
        pyautogui.press("win")
        pyautogui.sleep(0.5)
        pyautogui.write(app_name)
        pyautogui.sleep(0.5)
        pyautogui.press("enter")
        
    def search_web(self, query: str):
        print(f"WindowsController: Searching web for {query}")
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        webbrowser.open(url)

    def open_url(self, url: str):
        if not url:
            return
        webbrowser.open(url)

    def close_app(self, app_name: str):
        if not app_name:
            return
        # taskkill is reliable for Windows desktop apps.
        subprocess.run(["taskkill", "/IM", f"{app_name}.exe", "/F"], capture_output=True, text=True)

    def type_text(self, text: str):
        if text:
            pyautogui.write(text, interval=config.WHATSAPP_TYPE_DELAY)

    def press_hotkey(self, keys):
        if isinstance(keys, str):
            keys = [k.strip() for k in keys.split("+") if k.strip()]
        if keys:
            pyautogui.hotkey(*keys)

    def clipboard_copy(self, text: str):
        pyperclip.copy(text or "")

    def clipboard_paste(self):
        pyautogui.hotkey("ctrl", "v")

    def send_whatsapp_message(self, contact_name: str, message: str):
        """
        WhatsApp automation flow:
        1) Open WhatsApp app
        2) Focus search and select contact
        3) Type message and send
        """
        if not contact_name or not message:
            raise ValueError("contact_name and message are required for WhatsApp messaging.")

        self.open_app("whatsapp")
        time.sleep(1.6)

        # WhatsApp desktop supports Ctrl+F / Ctrl+K search in many builds.
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "k")
        time.sleep(config.WHATSAPP_SEARCH_DELAY)
        pyautogui.write(contact_name, interval=config.WHATSAPP_TYPE_DELAY)
        time.sleep(config.WHATSAPP_SEARCH_DELAY)
        pyautogui.press("enter")
        time.sleep(0.5)
        pyautogui.write(message, interval=config.WHATSAPP_TYPE_DELAY)
        pyautogui.press("enter")
