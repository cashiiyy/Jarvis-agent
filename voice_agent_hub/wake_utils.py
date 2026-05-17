"""
wake_utils.py — Shared wake-word detection utilities for JARVIS
================================================================
Combines three strategies so that casual/accented/quiet speech works:

  1. Regex phonetic patterns  — catches the 20+ most common Whisper mishearings
  2. rapidfuzz token ratio    — catches anything within ~70 % similarity
  3. Syllable anchor check    — if any word sounds like "jarvis" it counts

Import and call:
    from wake_utils import is_wake_word, extract_inline_command
"""
import re
import logging
from difflib import SequenceMatcher

# Try rapidfuzz (faster); fall back to stdlib difflib gracefully
try:
    from rapidfuzz import fuzz as _rfuzz
    def _similarity(a: str, b: str) -> float:
        return _rfuzz.token_set_ratio(a, b) / 100.0
except ImportError:
    def _similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

logger = logging.getLogger("jarvis.wake")

# ---------------------------------------------------------------------------
# 1.  Regex pattern bank — every documented Whisper mishearing of "Hey Jarvis"
# ---------------------------------------------------------------------------
_WAKE_PATTERNS = [
    # ── Correct ──────────────────────────────────────────────────────────
    r"\bhey\s+jarvis\b",
    r"\bhey,?\s+jarv\b",
    # ── 'hey' variants ────────────────────────────────────────────────────
    r"\bhi\s+jarvis\b",
    r"\bhay\s+jarvis\b",
    r"\baye\s+jarvis\b",
    r"\byo\s+jarvis\b",
    r"\boh\s+jarvis\b",
    r"\beh\s+jarvis\b",
    r"\ba\s+jarvis\b",          # Whisper drops 'h'
    # ── 'jarvis' variants (phonetic mishears) ─────────────────────────────
    r"\bhey\s+jarv\b",
    r"\bhey\s+jarbis\b",
    r"\bhey\s+jarbes\b",
    r"\bhey\s+jarves\b",
    r"\bhey\s+jarbus\b",
    r"\bhey\s+jervis\b",
    r"\bhey\s+jerv\b",
    r"\bhey\s+jarvice\b",
    r"\bhey\s+jarwis\b",
    r"\bhey\s+davis\b",         # very common Whisper substitution
    r"\bhey\s+dav\b",
    r"\bhey\s+arvis\b",         # 'j' dropped
    r"\ba\s+arvis\b",
    r"\bhey\s+jars\b",
    r"\bhey\s+harvest\b",
    r"\bhey\s+harbor\b",
    # ── 'hey' dropped entirely ────────────────────────────────────────────
    r"^jarvis\b",
    r"\bjarvis\b",              # lone 'jarvis' anywhere in text
    r"^jarbis\b",
    r"^jervis\b",
    # ── Multi-word casual ─────────────────────────────────────────────────
    r"\bhey\s+there\s+jarvis\b",
    r"\bok\s+jarvis\b",
    r"\bokay\s+jarvis\b",
]

_WAKE_RE = re.compile("|".join(_WAKE_PATTERNS), re.IGNORECASE)

# Used to split inline command from wake-word prefix
_WAKE_SPLIT_RE = re.compile(
    r"(?:hey|hi|yo|hay|aye|oh|a|ok|okay)?\s*"
    r"(?:jarvis|jarbis|jervis|jarv|jarvice|jarwis|jarves|jarbus|davis|arvis|harvest|harbor)",
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# 2.  Syllable-anchor heuristic
# ---------------------------------------------------------------------------
# If the Jaro-Winkler distance of any word to "jarvis" is high enough, accept it.
_JARVIS_ANCHORS = ["jarvis", "jarv", "jervis", "jarbis", "davis"]


def _word_is_jarvis_like(word: str) -> bool:
    word = word.lower().strip()
    if len(word) < 4:
        return False
    for anchor in _JARVIS_ANCHORS:
        if _similarity(word, anchor) >= 0.72:
            return True
    return False


def _any_word_is_jarvis(text: str) -> bool:
    words = re.sub(r"[^\w\s]", " ", text.lower()).split()
    return any(_word_is_jarvis_like(w) for w in words)


# ---------------------------------------------------------------------------
# 3.  Full-phrase similarity fallback
# ---------------------------------------------------------------------------
_WAKE_CANDIDATES = [
    "hey jarvis",
    "hi jarvis",
    "yo jarvis",
    "hey jervis",
    "ok jarvis",
    "jarvis",
]


def _phrase_similar_enough(text: str) -> bool:
    """True if the cleaned text is within 68 % token-set similarity to any candidate."""
    clean = re.sub(r"[^\w\s]", " ", text.lower()).strip()
    # Only consider the first 5 words (wake phrase is short)
    short = " ".join(clean.split()[:5])
    for cand in _WAKE_CANDIDATES:
        if _similarity(short, cand) >= 0.68:
            logger.debug("Fuzzy match '%s' ~ '%s'", short, cand)
            return True
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def is_wake_word(text: str) -> bool:
    """
    Return True if *text* contains a plausible 'Hey Jarvis' utterance.

    Uses three independent strategies — regex, syllable anchor, and fuzzy
    phrase similarity — and accepts if ANY of them fires.
    """
    if not text or not text.strip():
        return False

    clean = re.sub(r"[^\w\s]", " ", text.lower()).strip()

    # Strategy 1: Regex
    if _WAKE_RE.search(clean):
        logger.debug("[Wake] regex match: '%s'", text)
        return True

    # Strategy 2: Any single word sounds like 'jarvis'
    if _any_word_is_jarvis(clean):
        logger.debug("[Wake] syllable anchor match: '%s'", text)
        return True

    # Strategy 3: Whole phrase fuzzy similarity
    if _phrase_similar_enough(clean):
        logger.debug("[Wake] fuzzy phrase match: '%s'", text)
        return True

    return False


def extract_inline_command(text: str) -> str:
    """
    If the text contains the wake word followed by a command in the same breath
    (e.g. "Hey Jarvis open WhatsApp on my phone"), return just the command part.
    Returns "" if nothing follows the wake word.
    """
    # Split on the wake-word trigger
    parts = _WAKE_SPLIT_RE.split(text, maxsplit=1)
    if len(parts) < 2:
        return ""
    after = parts[-1]
    # Strip leading punctuation / whitespace
    after = re.sub(r"^[^\w]+", "", after).strip()
    return after
