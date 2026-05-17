"""
skills/youtube_skill.py
========================
YouTube automation via Android ADB.

Workflow:
  1. Open YouTube
  2. Wait for load
  3. Tap search icon (keyevent 84 = SEARCH)
  4. Type search query
  5. Press Enter
"""
import os
import sys
import time
import logging
from typing import Tuple

logger = logging.getLogger("jarvis.youtube")

_hub = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _hub not in sys.path:
    sys.path.insert(0, _hub)
from android_launcher import adb_shell, adb_launch_app, adb_connect  # noqa: E402


def search_youtube(
    device_ip: str,
    query: str,
    load_wait: float = 3.0,
) -> Tuple[bool, str]:
    """
    Open YouTube on device and search for query.
    Returns (success, message).
    """
    logger.info("[YT] Searching YouTube for '%s' on %s", query, device_ip)

    if not adb_connect(device_ip):
        return False, "Cannot reach device."

    # 1. Open YouTube
    ok, msg = adb_launch_app(device_ip, "youtube")
    if not ok:
        return False, f"Could not open YouTube: {msg}"
    logger.info("[YT] YouTube launched, waiting %.1fs for load", load_wait)
    time.sleep(load_wait)

    # 2. Press the search key to open the search bar
    adb_shell(device_ip, "input keyevent 84")
    time.sleep(0.8)

    # 3. Clear any existing text and type query
    adb_shell(device_ip, "input keyevent 123")   # KEYCODE_MOVE_END
    safe_query = query.replace(" ", "%s")
    adb_shell(device_ip, f"input text {safe_query}")
    time.sleep(0.5)

    # 4. Press Enter to search
    adb_shell(device_ip, "input keyevent 66")
    logger.info("[YT] Search submitted: '%s'", query)

    return True, f"Searching YouTube for '{query}'."


def open_youtube(device_ip: str) -> Tuple[bool, str]:
    """Just open YouTube without searching."""
    adb_connect(device_ip)
    return adb_launch_app(device_ip, "youtube")
