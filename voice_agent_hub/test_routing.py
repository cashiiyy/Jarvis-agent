import sys, re
sys.path.insert(0, ".")

_PHONE_NATIVE = {
    "whatsapp","instagram","snapchat","tiktok","telegram",
    "spotify","netflix","youtube","facebook","twitter","zoom",
    "phonepe","paytm","swiggy","zomato","uber","insta","fb","tg","yt",
}
_LAPTOP_RE = re.compile(r"\bon my\s+(laptop|computer|pc|windows|desktop)\b", re.I)
_PHONE_RE  = re.compile(r"\bon my\s+(phone|mobile|android|handset)\b", re.I)
_TABLET_RE = re.compile(r"\bon my\s+(tablet|tab|ipad)\b", re.I)

def classify(intent):
    lower = intent.lower()
    if _LAPTOP_RE.search(lower): return "laptop"
    if _PHONE_RE.search(lower):  return "phone"
    if _TABLET_RE.search(lower): return "tablet"
    words   = re.sub(r"[^\w\s]", " ", lower).split()
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
    for t in words + bigrams:
        if t in _PHONE_NATIVE:
            return "phone"
    return "laptop"

tests = [
    ("open whatsapp",                "phone"),
    ("open instagram",               "phone"),
    ("open youtube",                 "phone"),
    ("open calculator on my tablet", "tablet"),
    ("open whatsapp on my laptop",   "laptop"),
    ("search for news",              "laptop"),
    ("open notepad",                 "laptop"),
    ("launch spotify",               "phone"),
    ("open telegram",                "phone"),
]

all_ok = True
for intent, exp in tests:
    got = classify(intent)
    ok = (got == exp)
    if not ok:
        all_ok = False
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {intent!r:42s} -> {got!r}")

print()
print("All routing correct!" if all_ok else "ROUTING FAILURES FOUND")
