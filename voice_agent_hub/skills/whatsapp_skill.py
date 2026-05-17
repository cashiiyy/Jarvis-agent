"""
skills/whatsapp_skill.py
=========================
WhatsApp automation via Android ADB.

Strategy:
  1. Resolve contact nickname -> phone number from contacts.json
  2. Open WhatsApp deep-link with pre-filled message
     (user taps Send — or we automate it via keyevent)
  3. If no phone number: open WhatsApp, search by name, open chat, type, send

Usage:
    from skills.whatsapp_skill import send_whatsapp_message
    success, msg = send_whatsapp_message(device_ip, "mummy", "hi")
"""
import os
import re
import sys
import json
import time
import logging
import urllib.parse
from typing import Optional, Tuple

logger = logging.getLogger("jarvis.whatsapp")

# Resolve android_launcher from parent
_hub = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _hub not in sys.path:
    sys.path.insert(0, _hub)
from android_launcher import adb_shell, adb_connect  # noqa: E402

# Load contacts
_CONTACTS_FILE = os.path.join(_hub, "contacts.json")

def _load_contacts() -> dict:
    try:
        with open(_CONTACTS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except Exception as e:
        logger.warning("Could not load contacts.json: %s", e)
        return {}

def resolve_contact(nickname: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve a spoken nickname to (display_name, whatsapp_number).
    Returns (None, None) if not found.
    """
    contacts = _load_contacts()
    key = nickname.lower().strip()
    if key in contacts:
        entry = contacts[key]
        return entry.get("name", key), entry.get("whatsapp")
    # Fuzzy: check if any key starts with the nickname
    for ckey, entry in contacts.items():
        if ckey.startswith(key) or key.startswith(ckey):
            return entry.get("name", ckey), entry.get("whatsapp")
    return None, None


def send_whatsapp_message(
    device_ip: str,
    contact_nickname: str,
    message: str,
    auto_send: bool = True,
) -> Tuple[bool, str]:
    """
    Send a WhatsApp message to a contact on the Android device.
    Returns (success, human_readable_message).
    """
    logger.info("[WA] Sending '%s' to '%s' on %s", message, contact_nickname, device_ip)

    # 1. Resolve contact
    display_name, phone = resolve_contact(contact_nickname)
    if not phone:
        return False, (
            f"I don't have a phone number for '{contact_nickname}'. "
            f"Please add it to contacts.json, sir."
        )

    logger.info("[WA] Contact resolved: %s -> %s", display_name, phone)

    # 2. Ensure device connected
    if not adb_connect(device_ip):
        return False, f"Cannot reach device {device_ip}. Check wireless ADB."

    # 3. Build WhatsApp deep-link URI
    encoded_msg = urllib.parse.quote(message)
    wa_uri = f"https://api.whatsapp.com/send?phone={phone}&text={encoded_msg}"

    logger.info("[WA] Opening deep link for phone=%s", phone)
    ok, out, err = adb_shell(
        device_ip,
        f"am start -a android.intent.action.VIEW -d \"{wa_uri}\"",
    )
    if not ok:
        logger.error("[WA] Failed to open deep link: %s", err)
        return False, "Failed to open WhatsApp."

    # 4. Wait for WhatsApp to load
    logger.info("[WA] Waiting for WhatsApp to load (2.5s)...")
    time.sleep(2.5)

    # 5. Auto-send by pressing Enter/Send key (keyevent 66)
    if auto_send:
        logger.info("[WA] Pressing Enter to send message")
        ok2, _, _ = adb_shell(device_ip, "input keyevent 66")
        if not ok2:
            logger.warning("[WA] Enter key failed — user may need to tap Send manually")
            return True, f"Message ready to send to {display_name}. Tap Send to confirm."

    result_msg = f"Message sent to {display_name}." if auto_send else f"Message ready for {display_name}."
    logger.info("[WA] %s", result_msg)
    return True, result_msg


def open_whatsapp_chat(device_ip: str, contact_nickname: str) -> Tuple[bool, str]:
    """Open WhatsApp and navigate to a contact's chat (no message)."""
    display_name, phone = resolve_contact(contact_nickname)
    if not phone:
        return False, f"No contact found for '{contact_nickname}'."

    adb_connect(device_ip)
    wa_uri = f"https://api.whatsapp.com/send?phone={phone}"
    ok, _, err = adb_shell(device_ip, f"am start -a android.intent.action.VIEW -d \"{wa_uri}\"")
    if ok:
        return True, f"Opened WhatsApp chat with {display_name}."
    return False, f"Failed to open chat: {err}"
