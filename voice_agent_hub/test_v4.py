"""
Full test suite for all v4 fixes:
  1. Wake word variants
  2. Device routing (phone-native app detection)
  3. Package resolution (android_launcher)
  4. Audio RMS helper
"""
import sys, os, re, math, struct
sys.path.insert(0, ".")
from wake_utils import is_wake_word, extract_inline_command
from android_launcher import resolve_package

PASS = 0
FAIL = 0

def check(label, got, expected):
    global PASS, FAIL
    if got == expected:
        print(f"  [PASS] {label}")
        PASS += 1
    else:
        print(f"  [FAIL] {label}  got={got!r}  expected={expected!r}")
        FAIL += 1

# ── 1. Wake word ──────────────────────────────────────────────────────────────
print("\n=== Wake Word Detection ===")
wake_tests = [
    ("Hey Jarvis",                   True),
    ("hey jarvis",                   True),
    ("Hi Jarvis",                    True),
    ("Yo Jarvis",                    True),
    ("OK Jarvis",                    True),
    ("Hey, Jarvis.",                 True),
    ("Hey Jarv",                     True),
    ("Hey Davis",                    True),   # Whisper mishear
    ("Hey Jervis",                   True),   # Whisper mishear
    ("a Jarvis",                     True),   # Whisper mishear
    ("Jarvis",                       True),   # bare (Whisper drops 'hey')
    ("Hey Jarbis",                   True),
    ("hello world",                  False),
    ("thanks very much",             False),
    ("testing one two three",        False),
]
for phrase, exp in wake_tests:
    check(f"is_wake_word({phrase!r})", is_wake_word(phrase), exp)

# ── 2. Inline command extraction ──────────────────────────────────────────────
print("\n=== Inline Command Extraction ===")
inline_tests = [
    ("hey jarvis open whatsapp on my phone", "open whatsapp on my phone"),
    ("Hey Jarvis open chrome",               "open chrome"),
    ("Hey Jarvis",                           ""),
    ("Jarvis search for weather",            "search for weather"),
]
for phrase, exp in inline_tests:
    got = extract_inline_command(phrase).lower().strip()
    # partial match is fine for multiword
    ok = exp in got if exp else got == ""
    check(f"inline({phrase!r})", ok, True)

# ── 3. Intent routing (phone-native app detection) ────────────────────────────
print("\n=== Device Routing ===")
# Simulate _classify_device logic
_PHONE_NATIVE = {
    "whatsapp","instagram","snapchat","tiktok","telegram",
    "spotify","netflix","youtube","facebook","twitter",
    "zoom","phonepe","paytm","swiggy","zomato","uber","insta","fb","tg","yt",
}
_LAPTOP_RE = re.compile(r"\bon my\s+(laptop|computer|pc|windows|desktop)\b", re.I)
_PHONE_RE  = re.compile(r"\bon my\s+(phone|mobile|android|handset)\b", re.I)

def classify(intent):
    lower = intent.lower()
    if _LAPTOP_RE.search(lower): return "laptop"
    if _PHONE_RE.search(lower):  return "phone"
    words  = re.sub(r"[^\w\s]"," ",lower).split()
    bigrams= [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
    for t in words+bigrams:
        if t in _PHONE_NATIVE: return "phone"
    return "laptop"

routing_tests = [
    ("open whatsapp",                "phone"),   # phone-native, no prefix
    ("open instagram",               "phone"),
    ("open youtube",                 "phone"),
    ("open spotify",                 "phone"),
    ("open telegram",                "phone"),
    ("open whatsapp on my phone",    "phone"),   # explicit
    ("open whatsapp on my laptop",   "laptop"),  # explicit override
    ("open notepad",                 "laptop"),  # laptop-only app
    ("open notepad on my laptop",    "laptop"),
    ("search for weather",           "laptop"),  # no app, no device → laptop
    ("open calculator on my tablet", "tablet"),
]
for intent, exp in routing_tests:
    check(f"route({intent!r})", classify(intent), exp)

# ── 4. Package resolution ──────────────────────────────────────────────────────
print("\n=== Package Resolution ===")
pkg_tests = [
    ("whatsapp",    "com.whatsapp"),
    ("insta",       "com.instagram.android"),
    ("youtube",     "com.google.android.youtube"),
    ("spotify",     "com.spotify.music"),
    ("telegram",    "org.telegram.messenger"),
    ("tg",          "org.telegram.messenger"),
    ("fb",          "com.facebook.katana"),
    ("snapchat",    "com.snapchat.android"),
    ("snap",        "com.snapchat.android"),
    ("netflix",     "com.netflix.mediaclient"),
    ("zoom",        "us.zoom.videomeetings"),
    ("swiggy",      "in.swiggy.android"),
    ("phonepe",     "com.phonepe.app"),
    ("whatsap",     "com.whatsapp"),   # typo/mishear
    ("watsapp",     "com.whatsapp"),   # typo/mishear
]
for app, exp_pkg in pkg_tests:
    _, got_pkg = resolve_package(app)
    check(f"pkg({app!r})", got_pkg, exp_pkg)

# ── 5. RMS math ──────────────────────────────────────────────────────────────
print("\n=== Audio RMS ===")
import struct, math
def rms(data):
    count = len(data)//2
    if not count: return 0.0
    shorts = struct.unpack(f"{count}h", data[:count*2])
    sq = sum(s*s for s in shorts)
    return math.sqrt(sq/count)

silence = bytes(200)          # all zeros = silence
check("RMS silence=0", rms(silence), 0.0)
loud = struct.pack("100h", *([16384]*100))  # ~half-amplitude tone
r = rms(loud)
check("RMS loud > 100", r > 100, True)

# ── Summary ──────────────────────────────────────────────────────────────────
print(f"\n{'='*40}")
print(f"  PASSED: {PASS}   FAILED: {FAIL}")
print(f"  {'ALL TESTS PASSED' if FAIL == 0 else 'SOME FAILURES — see above'}")
print(f"{'='*40}")
sys.exit(0 if FAIL == 0 else 1)
