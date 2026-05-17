"""
core/active_device_manager.py
==============================
Manages which device JARVIS sends commands to by default.

Usage:
    from core.active_device_manager import get_device_manager
    mgr = get_device_manager()
    mgr.active          # -> "phone" / "laptop" / "tablet"
    mgr.set_device("phone")
    mgr.detect_set_command("switch to phone")  # -> "phone" or None
"""
import re
import logging
from typing import Optional

logger = logging.getLogger("jarvis.device_mgr")

DEVICE_PHONE  = "phone"
DEVICE_TABLET = "tablet"
DEVICE_LAPTOP = "laptop"
VALID_DEVICES = {DEVICE_PHONE, DEVICE_TABLET, DEVICE_LAPTOP}

DEVICE_ALIASES = {
    "phone": DEVICE_PHONE, "mobile": DEVICE_PHONE, "android": DEVICE_PHONE,
    "handset": DEVICE_PHONE, "cell": DEVICE_PHONE, "smartphone": DEVICE_PHONE,
    "tablet": DEVICE_TABLET, "tab": DEVICE_TABLET, "ipad": DEVICE_TABLET,
    "laptop": DEVICE_LAPTOP, "computer": DEVICE_LAPTOP, "pc": DEVICE_LAPTOP,
    "windows": DEVICE_LAPTOP, "desktop": DEVICE_LAPTOP, "mac": DEVICE_LAPTOP,
}
DEVICE_LABELS = {
    DEVICE_PHONE: "Android phone",
    DEVICE_TABLET: "tablet",
    DEVICE_LAPTOP: "laptop",
}

# Patterns that indicate a set-device command
_SET_RE = re.compile(
    r"(?:set|switch|make|change|use|activate)\s+(?:default\s+)?(?:device\s+)?"
    r"(?:to\s+)?(?:my\s+)?"
    r"(phone|mobile|android|handset|cell|smartphone"
    r"|tablet|tab|ipad"
    r"|laptop|computer|pc|windows|desktop|mac)"
    r"(?:\s+(?:as|the|my)\s+(?:active|default|primary))?",
    re.IGNORECASE,
)
_QUERY_RE = re.compile(
    r"(?:what|which|current|active|default)\s+(?:is\s+)?(?:the\s+)?(?:active|default|current\s+)?"
    r"device|current\s+device",
    re.IGNORECASE,
)


class ActiveDeviceManager:
    def __init__(self, default: str = DEVICE_PHONE):
        self._active = default
        logger.info("Device manager ready — default=%s", self._active)

    @property
    def active(self) -> str:
        return self._active

    @property
    def active_label(self) -> str:
        return DEVICE_LABELS.get(self._active, self._active)

    def set_device(self, spoken_name: str) -> Optional[str]:
        """Set active device. Returns canonical name or None if unrecognised."""
        key = spoken_name.lower().strip()
        # Strip trailing filler words
        key = re.sub(r"\s+(?:device|as|the|my|a|please)$", "", key).strip()
        canonical = DEVICE_ALIASES.get(key)
        if canonical:
            old = self._active
            self._active = canonical
            logger.info("Active device: %s -> %s", old, canonical)
            return canonical
        return None

    def detect_set_command(self, text: str) -> Optional[str]:
        """
        If text is a 'set device' command, update and return new device label.
        Returns None if not a device-set command.
        """
        m = _SET_RE.search(text)
        if m:
            candidate = m.group(1).strip()
            result = self.set_device(candidate)
            if result:
                return DEVICE_LABELS[result]
        return None

    def is_query(self, text: str) -> bool:
        return bool(_QUERY_RE.search(text))

    def query_response(self) -> str:
        return f"The active device is your {self.active_label}, sir."


# Module-level singleton
_mgr: Optional[ActiveDeviceManager] = None

def get_device_manager() -> ActiveDeviceManager:
    global _mgr
    if _mgr is None:
        _mgr = ActiveDeviceManager(default=DEVICE_PHONE)
    return _mgr
