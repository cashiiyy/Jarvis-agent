"""
core/command_parser.py
=======================
Extracts structured entities from a raw voice command string.

Returns a ParsedCommand dataclass with:
  action, app_target, device_target, contact_name, message_body,
  search_query, steps (for multi-step commands)
"""
import re
import logging
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger("jarvis.parser")

# ── Device alias map ──────────────────────────────────────────────────────────
DEVICE_ALIASES = {
    "phone": "phone", "mobile": "phone", "android": "phone",
    "handset": "phone", "cell": "phone", "smartphone": "phone",
    "tablet": "tablet", "tab": "tablet", "ipad": "tablet",
    "laptop": "laptop", "computer": "laptop", "pc": "laptop",
    "windows": "laptop", "desktop": "laptop", "mac": "laptop",
}

_DEVICE_RE = re.compile(
    r"\b(?:on|in|at|using|via|for|to)\s+(?:my\s+)?"
    r"(phone|mobile|android|handset|cell|smartphone"
    r"|tablet|tab|ipad"
    r"|laptop|computer|pc|windows|desktop|mac)\b",
    re.IGNORECASE,
)
_STEP_SPLIT_RE = re.compile(r"\s+(?:and|then|after\s+that)\s+", re.IGNORECASE)
_OPEN_RE   = re.compile(r"(?:open|launch|start|run|show|play)\s+([a-z0-9 ]+?)(?=\s+(?:and|then|on|in|$)|$)", re.I)
_SEARCH_RE = re.compile(r"(?:search(?:\s+for)?|find|look\s+up|google)\s+(.+?)(?=\s+(?:on|in|and|then|$)|$)", re.I)
_SEND1_RE  = re.compile(r"(?:send|text|msg)\s+(.+?)\s+to\s+([a-z0-9]+)(?:\s+(?:on|in|via|through)\s+(\w+))?", re.I)
_SEND2_RE  = re.compile(r"(?:message|whatsapp|tell)\s+([a-z0-9]+)\s+(.+)", re.I)
_WAKE_RE   = re.compile(r"^(?:hey\s+jarvis[,.]?\s*)", re.IGNORECASE)


@dataclass
class ParsedCommand:
    raw_text: str
    action: Optional[str]       = None
    app_target: Optional[str]   = None
    device_target: Optional[str]= None
    contact_name: Optional[str] = None
    message_body: Optional[str] = None
    search_query: Optional[str] = None
    steps: List[str]            = field(default_factory=list)

    def __str__(self):
        parts = []
        for k in ("action","app_target","device_target","contact_name","message_body","search_query"):
            v = getattr(self, k)
            if v: parts.append(f"{k}={v!r}")
        if self.steps: parts.append(f"steps={len(self.steps)}")
        return "Cmd(" + " ".join(parts) + ")"


def parse(raw: str) -> ParsedCommand:
    cmd = ParsedCommand(raw_text=raw)
    text = _WAKE_RE.sub("", raw).strip()

    # Device
    dm = _DEVICE_RE.search(text)
    if dm:
        cmd.device_target = DEVICE_ALIASES.get(dm.group(1).lower())
    text_clean = _DEVICE_RE.sub("", text).strip()

    # Multi-step split
    steps = _STEP_SPLIT_RE.split(text_clean)
    if len(steps) > 1:
        cmd.steps = [s.strip() for s in steps if s.strip()]
    primary = steps[0].strip()

    # Send message patterns (check before open so "send X to Y" wins)
    m = _SEND1_RE.search(primary)
    if m:
        cmd.action        = "send"
        cmd.message_body  = m.group(1).strip()
        cmd.contact_name  = m.group(2).strip().lower()
        if m.group(3):
            cmd.app_target = m.group(3).strip().lower()
    else:
        m = _SEND2_RE.search(primary)
        if m:
            cmd.action       = "send"
            cmd.contact_name = m.group(1).strip().lower()
            cmd.message_body = m.group(2).strip()

    # Open app
    if not cmd.action:
        m = _OPEN_RE.match(primary)
        if m:
            cmd.action     = "open"
            raw_app = re.sub(r"\s*(app|application)$", "", m.group(1), flags=re.I).strip()
            cmd.app_target = raw_app.lower()

    # Search
    if not cmd.action:
        m = _SEARCH_RE.search(primary)
        if m:
            cmd.action       = "search"
            cmd.search_query = m.group(1).strip()

    # Generic fallback action word
    if not cmd.action:
        first_word = primary.split()[0].lower() if primary.split() else ""
        if first_word in {"open","launch","start","send","search","switch","set","use","make"}:
            cmd.action = first_word

    logger.info("[Parser] %s", cmd)
    return cmd
