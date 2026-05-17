import os
import re
import subprocess
import time
import urllib.parse
import webbrowser

from jarvis_automation.windows_controller import WindowsController
from jarvis_mobile.adb_manager import ADBManager
from jarvis_mobile.android_controller import AndroidController
from jarvis_core.config import config


class DeviceRouter:
    def __init__(self):
        self.windows = WindowsController()

        # Phone
        try:
            phone_adb = ADBManager()
            phone_ip, phone_port = self._split_ip_port(config.MOBILE_IP_PORT)
            phone_adb.connect_wireless(phone_ip, phone_port)
            self.android_phone = AndroidController(phone_adb, config.MOBILE_IP_PORT)
            print(f"[Router] Phone ADB ready → {config.MOBILE_IP_PORT}")
        except Exception as e:
            print(f"[Router] Warning: Phone ADB failed ({e}). Mobile control disabled.")
            self.android_phone = None

        # Tablet (separate ADB manager to keep serials independent)
        try:
            tablet_adb = ADBManager()
            tablet_ip, tablet_port = self._split_ip_port(config.TABLET_IP_PORT)
            tablet_adb.connect_wireless(tablet_ip, tablet_port)
            self.android_tablet = AndroidController(tablet_adb, config.TABLET_IP_PORT)
            print(f"[Router] Tablet ADB ready → {config.TABLET_IP_PORT}")
        except Exception as e:
            print(f"[Router] Warning: Tablet ADB failed ({e}). Tablet control disabled.")
            self.android_tablet = None

    # ------------------------------------------------------------------ #
    @staticmethod
    def _split_ip_port(ip_port: str):
        """Split '192.168.1.7:5555' → ('192.168.1.7', 5555)."""
        parts = ip_port.rsplit(":", 1)
        return parts[0], int(parts[1]) if len(parts) > 1 else 5555

    # ------------------------------------------------------------------ #
    def route_intent(self, intent: dict):
        target = (intent.get("target_device") or "laptop").lower()
        action = (intent.get("action") or "chat").lower()
        params = intent.get("parameters") or {}

        print(f"[Router] Routing action='{action}' → device='{target}'")

        if target == "phone":
            self._execute_android(self.android_phone, action, params, label="phone")
        elif target == "tablet":
            self._execute_android(self.android_tablet, action, params, label="tablet")
        else:
            # laptop / default
            self._execute_laptop(action, params)

    # ------------------------------------------------------------------ #
    def _execute_android(self, controller, action: str, params: dict, label: str):
        if controller is None:
            print(f"[Router] {label.title()} not connected — skipping.")
            return

        if action == "open_app":
            controller.open_app(params.get("app_name", ""))
        elif action == "send_message":
            # On Android we only do basic ADB text input for now
            msg = params.get("message", "")
            if msg:
                controller.send_text(msg)
        else:
            print(f"[Router] Unhandled action '{action}' for {label}.")

    # ------------------------------------------------------------------ #
    def _execute_laptop(self, action: str, params: dict):
        if action == "open_app":
            self.windows.open_app(params.get("app_name", ""))
        elif action == "search_web":
            self.windows.search_web(params.get("query", ""))
        elif action == "send_message":
            channel = (params.get("channel") or "whatsapp").lower()
            if channel == "whatsapp":
                self.windows.send_whatsapp_message(
                    params.get("contact_name", ""),
                    params.get("message", ""),
                )
        elif action == "system_control":
            operation = (params.get("operation") or "").lower()
            if operation == "close_app":
                self.windows.close_app(params.get("app_name", ""))
            elif operation == "type_text":
                self.windows.type_text(params.get("text", ""))
            elif operation == "hotkey":
                self.windows.press_hotkey(params.get("keys", []))
            elif operation == "clipboard_copy":
                self.windows.clipboard_copy(params.get("text", ""))
            elif operation == "clipboard_paste":
                self.windows.clipboard_paste()
        elif action == "chat":
            # Nothing to do at router level — TTS handled in main
            pass
        else:
            print(f"[Router] Unknown action: {action}")
