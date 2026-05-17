"""
JarvisAssistant — Android Controller
======================================
Delegates actual ADB execution to the shared android_launcher module
(voice_agent_hub/android_launcher.py), which provides:
  - 80+ app-package mappings
  - Fuzzy app-name resolution
  - 3-strategy launch with retry
  - Full structured logging
"""
import logging
import sys
import os

from jarvis_mobile.adb_manager import ADBManager

# Share android_launcher from voice_agent_hub
_hub_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "voice_agent_hub")
)
if _hub_dir not in sys.path:
    sys.path.insert(0, _hub_dir)

from android_launcher import (   # noqa: E402
    adb_launch_app,
    adb_connect,
    adb_shell,
    log_device_info,
)

logger = logging.getLogger("jarvis.android_controller")


class AndroidController:
    def __init__(self, adb_manager: ADBManager, device_serial: str = None):
        self.adb_manager = adb_manager
        self.device_serial = device_serial   # e.g. "192.168.1.7:5555"
        self.device = self.adb_manager.get_device(device_serial)

        if device_serial:
            logger.info("AndroidController initialised for %s", device_serial)
            log_device_info(device_serial)

    # ------------------------------------------------------------------ #
    def _refresh_device(self):
        """Re-query ADB — call before any operation in case device reconnected."""
        self.device = self.adb_manager.get_device(self.device_serial)

    # ------------------------------------------------------------------ #
    def open_app(self, app_name: str) -> bool:
        """
        Launch an app on the device.
        Uses android_launcher for fuzzy name resolution + multi-strategy ADB launch.
        Returns True on success.
        """
        if not self.device_serial:
            logger.error("No device serial configured — cannot launch app")
            return False

        # Ensure device is connected
        connected = adb_connect(self.device_serial)
        if not connected:
            logger.error("Device %s not reachable", self.device_serial)
            return False

        logger.info("Launching app '%s' on %s", app_name, self.device_serial)
        success, message = adb_launch_app(self.device_serial, app_name)
        if success:
            logger.info("[OK] %s", message)
        else:
            logger.error("[FAIL] %s", message)
        return success

    # ------------------------------------------------------------------ #
    def send_text(self, text: str):
        if not self.device_serial:
            return
        formatted = text.replace(" ", "%s")
        ok, out, err = adb_shell(self.device_serial, f"input text {formatted}")
        if not ok:
            logger.warning("send_text failed: %s", err)

    def tap(self, x: int, y: int):
        if not self.device_serial:
            return
        adb_shell(self.device_serial, f"input tap {x} {y}")

    def press_back(self):
        if self.device_serial:
            adb_shell(self.device_serial, "input keyevent 4")

    def press_home(self):
        if self.device_serial:
            adb_shell(self.device_serial, "input keyevent 3")

    def press_recent_apps(self):
        if self.device_serial:
            adb_shell(self.device_serial, "input keyevent 187")

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
        if self.device_serial:
            adb_shell(self.device_serial,
                      f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")

    def screenshot(self, local_path: str = "screenshot.png"):
        """Pull a screenshot from the device."""
        if not self.device_serial:
            return False
        ok, _, _ = adb_shell(self.device_serial, "screencap -p /sdcard/tmp_sc.png")
        if not ok:
            return False
        try:
            import subprocess
            subprocess.run(
                ["adb", "-s", self.device_serial, "pull", "/sdcard/tmp_sc.png", local_path],
                capture_output=True, timeout=10,
            )
            logger.info("Screenshot saved to %s", local_path)
            return True
        except Exception as exc:
            logger.error("Screenshot pull failed: %s", exc)
            return False
