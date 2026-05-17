import sys
sys.path.insert(0, ".")
from android_launcher import resolve_package

apps = [
    "whatsapp", "what app", "insta", "ig", "you tube",
    "youtube", "chrome", "google chrome", "settings",
    "spotify", "netflix", "telegram", "tg", "maps",
    "calculator", "camera", "gmail", "facebook", "fb",
    "snapchat", "snap", "tiktok", "tik tok", "zoom",
    "phonepe", "phone pay", "paytm", "swiggy", "zomato",
    "whatsap", "watsapp",
]

print("Package resolution tests:")
print("-" * 60)
all_ok = True
for app in apps:
    canonical, pkg = resolve_package(app)
    status = "PASS" if pkg else "FAIL"
    if not pkg:
        all_ok = False
    print(f"  [{status}] {app!r:25s} -> {canonical!r:20s}  {pkg or 'NOT FOUND'}")

print()
print("All resolved!" if all_ok else "Some apps not resolved")
