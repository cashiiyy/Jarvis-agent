"""
core/intent_classifier.py
===========================
Classifies a command string into an IntentType.

Priority order (checked top-down):
  DEVICE_SWITCH > DEVICE_QUERY > SEND_MESSAGE > MULTISTEP > OPEN_APP > SEARCH > UNKNOWN
"""
import re
import logging
from enum import Enum
from typing import Tuple

logger = logging.getLogger("jarvis.intent")


class Intent(Enum):
    DEVICE_SWITCH  = "DEVICE_SWITCH"   # "switch to phone"
    DEVICE_QUERY   = "DEVICE_QUERY"    # "current device?"
    SEND_MESSAGE   = "SEND_MESSAGE"    # "send hi to mummy"
    MULTISTEP      = "MULTISTEP"       # "open WA and send hi to mom"
    OPEN_APP       = "OPEN_APP"        # "open whatsapp"
    SEARCH         = "SEARCH"          # "search lo-fi music"
    UNKNOWN        = "UNKNOWN"


_DEVICE_NAMES = r"(?:phone|mobile|android|handset|tablet|tab|ipad|laptop|computer|pc|windows|desktop)"

_PATTERNS: list[Tuple[Intent, re.Pattern]] = [
    # Device switch — must be before OPEN_APP
    (Intent.DEVICE_SWITCH, re.compile(
        r"(?:set|switch|make|change|use|activate)\s+(?:default\s+)?(?:device\s+)?(?:to\s+)?" + _DEVICE_NAMES,
        re.IGNORECASE)),
    (Intent.DEVICE_SWITCH, re.compile(
        r"switch\s+to\s+" + _DEVICE_NAMES, re.IGNORECASE)),

    # Device query
    (Intent.DEVICE_QUERY, re.compile(
        r"(?:what|which|current|active|default)\s+(?:is\s+)?(?:the\s+)?(?:active|default|current\s+)?device"
        r"|current\s+device", re.IGNORECASE)),

    # Multistep — must have an open/launch AND another action word separated by 'and/then'
    # e.g. "open whatsapp and send hi to mom" | "open youtube then search lofi"
    (Intent.MULTISTEP, re.compile(
        r"(?:open|launch|start)\s+\w.+\s+(?:and|then|after\s+that)\s+(?:send|search|find|play|type|go|open|launch)",
        re.IGNORECASE)),

    # Messaging — "send X to Y", "text Y X", "message Y X", "whatsapp Y"
    (Intent.SEND_MESSAGE, re.compile(
        r"(?:send|text|message|msg|whatsapp|tell|say)\s+.{2,}\s+to\s+\w", re.IGNORECASE)),
    (Intent.SEND_MESSAGE, re.compile(
        r"(?:message|text|whatsapp|tell)\s+[a-z]+\s+.{2,}", re.IGNORECASE)),

    # Open app
    (Intent.OPEN_APP, re.compile(
        r"(?:open|launch|start|run|show|play)\s+\w", re.IGNORECASE)),

    # Search
    (Intent.SEARCH, re.compile(
        r"(?:search(?:\s+for)?|find|look\s+up|google)\s+\w", re.IGNORECASE)),
]



def classify(text: str) -> Intent:
    for intent, pat in _PATTERNS:
        if pat.search(text):
            logger.info("[Intent] %s <- '%s'", intent.value, text[:60])
            return intent
    logger.info("[Intent] UNKNOWN <- '%s'", text[:60])
    return Intent.UNKNOWN
