"""
android_launcher.py — Reliable ADB app-launch engine for JARVIS
================================================================
Provides:
  - adb_connect()       : Connect / verify a wireless ADB device
  - adb_launch_app()    : Launch an Android app with multiple fallback strategies
  - resolve_package()   : Fuzzy app-name → package-name resolution
  - adb_shell()         : Raw ADB shell with logging + timeout

All functions are safe to call from both sync and async contexts.
"""
import re
import logging
import subprocess
import time
from typing import Optional, Tuple

try:
    from rapidfuzz import process as _rfprocess, fuzz as _rfuzz
    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False

logger = logging.getLogger("jarvis.android")

# ---------------------------------------------------------------------------
# Comprehensive app-name → package mapping
# ---------------------------------------------------------------------------
APP_PACKAGES: dict[str, str] = {
    # Messaging
    "whatsapp":             "com.whatsapp",
    "whatsapp business":    "com.whatsapp.w4b",
    "telegram":             "org.telegram.messenger",
    "signal":               "org.thoughtcrime.securesms",
    "messenger":            "com.facebook.orca",
    "discord":              "com.discord",
    "slack":                "com.slack",
    "skype":                "com.skype.raider",
    "viber":                "com.viber.voip",
    "line":                 "jp.naver.line.android",
    "wechat":               "com.tencent.mm",
    # Social
    "instagram":            "com.instagram.android",
    "facebook":             "com.facebook.katana",
    "twitter":              "com.twitter.android",
    "x":                    "com.twitter.android",
    "snapchat":             "com.snapchat.android",
    "tiktok":               "com.zhiliaoapp.musically",
    "pinterest":            "com.pinterest",
    "linkedin":             "com.linkedin.android",
    "reddit":               "com.reddit.frontpage",
    "threads":              "com.instagram.barcelona",
    # Video / Streaming
    "youtube":              "com.google.android.youtube",
    "youtube music":        "com.google.android.apps.youtube.music",
    "netflix":              "com.netflix.mediaclient",
    "prime video":          "com.amazon.avod.thirdpartyclient",
    "amazon prime":         "com.amazon.avod.thirdpartyclient",
    "hotstar":              "in.startv.hotstar",
    "disney hotstar":       "in.startv.hotstar",
    "disney":               "in.startv.hotstar",
    "zee5":                 "com.zee5.app",
    "sonyliv":              "com.sonyiv.android",
    "mx player":            "com.mxtech.videoplayer.ad",
    "vlc":                  "org.videolan.vlc",
    # Music
    "spotify":              "com.spotify.music",
    "gaana":                "com.gaana",
    "jio saavn":            "com.jio.media.jiobeats",
    "saavn":                "com.jio.media.jiobeats",
    "wynk":                 "com.bsbportal.music",
    "amazon music":         "com.amazon.mp3",
    # Google apps
    "gmail":                "com.google.android.gm",
    "maps":                 "com.google.android.apps.maps",
    "google maps":          "com.google.android.apps.maps",
    "chrome":               "com.android.chrome",
    "google chrome":        "com.android.chrome",
    "drive":                "com.google.android.apps.docs",
    "google drive":         "com.google.android.apps.docs",
    "photos":               "com.google.android.apps.photos",
    "google photos":        "com.google.android.apps.photos",
    "google pay":           "com.google.android.apps.nbu.paisa.user",
    "gpay":                 "com.google.android.apps.nbu.paisa.user",
    "meet":                 "com.google.android.apps.meetings",
    "google meet":          "com.google.android.apps.meetings",
    "docs":                 "com.google.android.apps.docs.editors.docs",
    "sheets":               "com.google.android.apps.docs.editors.sheets",
    "slides":               "com.google.android.apps.docs.editors.slides",
    "keep":                 "com.google.android.keep",
    "google keep":          "com.google.android.keep",
    "duo":                  "com.google.android.apps.tachyon",
    # System / Utilities
    "settings":             "com.android.settings",
    "camera":               "com.android.camera2",
    "calculator":           "com.google.android.calculator",
    "clock":                "com.google.android.deskclock",
    "calendar":             "com.google.android.calendar",
    "contacts":             "com.google.android.contacts",
    "phone":                "com.google.android.dialer",
    "dialer":               "com.google.android.dialer",
    "messages":             "com.google.android.apps.messaging",
    "gallery":              "com.sec.android.gallery3d",
    "file manager":         "com.google.android.apps.nbu.files",
    "files":                "com.google.android.apps.nbu.files",
    "play store":           "com.android.vending",
    "app store":            "com.android.vending",
    # Finance / Payments
    "phonepe":              "com.phonepe.app",
    "paytm":                "net.one97.paytm",
    "bhim":                 "in.org.npci.upiapp",
    "amazon":               "com.amazon.mShop.android.shopping",
    "flipkart":             "com.flipkart.android",
    # Productivity
    "zoom":                 "us.zoom.videomeetings",
    "teams":                "com.microsoft.teams",
    "microsoft teams":      "com.microsoft.teams",
    "word":                 "com.microsoft.office.word",
    "excel":                "com.microsoft.office.excel",
    "powerpoint":           "com.microsoft.office.powerpoint",
    "outlook":              "com.microsoft.office.outlook",
    "notion":               "notion.id",
    "trello":               "com.trello",
    # Navigation / Travel
    "uber":                 "com.ubercab",
    "ola":                  "com.olacabs.customer",
    "rapido":               "com.rapido.passenger",
    "swiggy":               "in.swiggy.android",
    "zomato":               "com.application.zomato",
    # Browser
    "firefox":              "org.mozilla.firefox",
    "brave":                "com.brave.browser",
    "opera":                "com.opera.browser",
    "edge":                 "com.microsoft.emmx",
    # Health / Fitness
    "health connect":       "com.google.android.apps.healthdata",
    "google fit":           "com.google.android.apps.fitness",
}

# Spoken-form aliases that map to canonical names above
_SPOKEN_ALIASES: dict[str, str] = {
    "whats app":            "whatsapp",
    "what's app":           "whatsapp",
    "what app":             "whatsapp",
    "you tube":             "youtube",
    "you-tube":             "youtube",
    "insta":                "instagram",
    "ig":                   "instagram",
    "fb":                   "facebook",
    "tele":                 "telegram",
    "tg":                   "telegram",
    "gmap":                 "maps",
    "google map":           "maps",
    "play":                 "play store",
    "camera app":           "camera",
    "snap":                 "snapchat",
    "tok":                  "tiktok",
    "tik tok":              "tiktok",
    "prime":                "prime video",
    "hotstar app":          "hotstar",
    "jio":                  "jio saavn",
    "music":                "spotify",
    "email":                "gmail",
    "mail":                 "gmail",
    "pay":                  "google pay",
    "g pay":                "google pay",
    "phone pay":            "phonepe",
    "phone pe":             "phonepe",
    "dialer":               "phone",
    "call app":             "phone",
}


# ---------------------------------------------------------------------------
# Package resolution
# ---------------------------------------------------------------------------
def resolve_package(app_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve a spoken/typed app name to (canonical_name, package_id).
    Returns (None, None) if nothing matches.

    Steps:
      1. Exact lookup
      2. Alias map
      3. Prefix match
      4. rapidfuzz fuzzy match (if available)
      5. difflib fallback
    """
    name = app_name.lower().strip()
    # Strip filler words users often add
    name = re.sub(r"\b(app|application|the|my)\b", "", name).strip()
    name = re.sub(r"\s{2,}", " ", name).strip()

    # 1. Exact
    if name in APP_PACKAGES:
        logger.info("[Package] Exact match '%s' -> %s", name, APP_PACKAGES[name])
        return name, APP_PACKAGES[name]

    # 2. Alias
    canonical = _SPOKEN_ALIASES.get(name)
    if canonical and canonical in APP_PACKAGES:
        logger.info("[Package] Alias '%s' -> '%s' -> %s", name, canonical, APP_PACKAGES[canonical])
        return canonical, APP_PACKAGES[canonical]

    # 3. Prefix / substring
    for key, pkg in APP_PACKAGES.items():
        if name in key or key in name:
            logger.info("[Package] Substring match '%s' ~ '%s' -> %s", name, key, pkg)
            return key, pkg

    # 4. rapidfuzz
    if _HAS_RAPIDFUZZ:
        result = _rfprocess.extractOne(
            name, APP_PACKAGES.keys(),
            scorer=_rfuzz.token_set_ratio,
            score_cutoff=70,
        )
        if result:
            best_key = result[0]
            logger.info("[Package] Fuzzy match '%s' ~ '%s' (%.0f%%) -> %s",
                        name, best_key, result[1], APP_PACKAGES[best_key])
            return best_key, APP_PACKAGES[best_key]

    # 5. difflib fallback
    from difflib import get_close_matches
    close = get_close_matches(name, APP_PACKAGES.keys(), n=1, cutoff=0.65)
    if close:
        best_key = close[0]
        logger.info("[Package] difflib match '%s' ~ '%s' -> %s", name, best_key, APP_PACKAGES[best_key])
        return best_key, APP_PACKAGES[best_key]

    logger.warning("[Package] No match found for '%s'", app_name)
    return None, None


# ---------------------------------------------------------------------------
# Core ADB helpers
# ---------------------------------------------------------------------------
def adb_shell(device_serial: str, command: str, timeout: int = 12) -> Tuple[bool, str, str]:
    """
    Run `adb -s <device_serial> shell <command>`.
    Returns (success, stdout, stderr).
    """
    cmd = ["adb", "-s", device_serial, "shell", command]
    logger.debug("[ADB] %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        success = result.returncode == 0
        if not success:
            logger.warning("[ADB] shell failed (rc=%d): %s", result.returncode, stderr or stdout)
        else:
            logger.debug("[ADB] stdout: %s", stdout[:200])
        return success, stdout, stderr
    except FileNotFoundError:
        logger.error("[ADB] adb binary not found in PATH")
        return False, "", "adb not found"
    except subprocess.TimeoutExpired:
        logger.error("[ADB] command timed out after %ds", timeout)
        return False, "", "timeout"
    except Exception as exc:
        logger.error("[ADB] unexpected error: %s", exc)
        return False, "", str(exc)


def adb_connect(device_serial: str, timeout: int = 8) -> bool:
    """
    Connect to a wireless ADB device.  Returns True if connected/already-connected.
    """
    logger.info("[ADB] Connecting to %s ...", device_serial)
    try:
        result = subprocess.run(
            ["adb", "connect", device_serial],
            capture_output=True, text=True, timeout=timeout
        )
        out = result.stdout.lower() + result.stderr.lower()
        if "connected" in out or "already connected" in out:
            logger.info("[ADB] Connected: %s", device_serial)
            return True
        logger.warning("[ADB] Connect failed for %s: %s", device_serial, result.stdout.strip())
        return False
    except Exception as exc:
        logger.error("[ADB] Connect error: %s", exc)
        return False


def _check_device_alive(device_serial: str) -> bool:
    """Ping device to confirm it's actually responding."""
    ok, out, _ = adb_shell(device_serial, "echo ping", timeout=5)
    return ok and "ping" in out


# ---------------------------------------------------------------------------
# App launch (with 3 fallback strategies + retry)
# ---------------------------------------------------------------------------
def adb_launch_app(
    device_serial: str,
    app_name: str,
    max_retries: int = 2,
) -> Tuple[bool, str]:
    """
    Launch an app on the connected Android device.

    Returns (success: bool, message: str).

    Strategies tried in order:
      1. monkey launcher  (fastest, most reliable)
      2. am start -n      (requires activity lookup, skipped if monkey works)
      3. am start with VIEW intent (URL fallback for web-capable apps)

    Retries up to max_retries times with a 1-second pause between.
    """
    # --- Resolve package -------------------------------------------------
    canonical, package = resolve_package(app_name)
    if not package:
        msg = f"I don't know the package for '{app_name}'. Add it to android_launcher.APP_PACKAGES."
        logger.error(msg)
        return False, msg

    logger.info("[Launch] %s -> %s on %s", canonical, package, device_serial)

    # --- Ensure device is connected --------------------------------------
    if not _check_device_alive(device_serial):
        logger.info("[Launch] Device not responding, trying to reconnect...")
        if not adb_connect(device_serial):
            return False, f"Device {device_serial} not reachable."
        time.sleep(0.8)

    # --- Strategy 1: monkey ---------------------------------------------
    for attempt in range(1, max_retries + 2):
        logger.info("[Launch] Attempt %d — monkey launcher for %s", attempt, package)
        ok, out, err = adb_shell(
            device_serial,
            f"monkey -p {package} -c android.intent.category.LAUNCHER 1",
        )
        if ok and "Events injected: 1" in out:
            msg = f"Opened {canonical} on your device."
            logger.info("[Launch] SUCCESS via monkey: %s", package)
            return True, msg
        # monkey may succeed even without "Events injected" on some ROMs
        if ok and "error" not in out.lower() and "exception" not in out.lower():
            msg = f"Opened {canonical} on your device."
            logger.info("[Launch] SUCCESS (no error in monkey output): %s", package)
            return True, msg

        logger.warning("[Launch] monkey attempt %d failed (out=%s | err=%s)", attempt, out[:80], err[:80])
        if attempt <= max_retries:
            time.sleep(1.0)

    # --- Strategy 2: am start -a MAIN  ----------------------------------
    logger.info("[Launch] Falling back to 'am start' for %s", package)
    ok, out, err = adb_shell(
        device_serial,
        f"am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n {package}/.MainActivity",
    )
    if ok and ("starting" in out.lower() or "activity" in out.lower()):
        msg = f"Opened {canonical} on your device (am start)."
        logger.info("[Launch] SUCCESS via am start")
        return True, msg

    # --- Strategy 3: am start package only (no activity name) -----------
    logger.info("[Launch] Falling back to package-only am start for %s", package)
    ok, out, err = adb_shell(
        device_serial,
        f"am start -n {package}",
    )
    if ok:
        msg = f"Opened {canonical} on your device."
        logger.info("[Launch] SUCCESS via am start (package only)")
        return True, msg

    err_msg = f"Failed to open '{canonical}' on {device_serial}. Check the device is unlocked and the app is installed."
    logger.error("[Launch] All strategies exhausted for %s. Last err: %s", package, err)
    return False, err_msg


# ---------------------------------------------------------------------------
# Convenience: quick device info log
# ---------------------------------------------------------------------------
def log_device_info(device_serial: str) -> None:
    """Log basic device info for diagnostics."""
    ok, out, _ = adb_shell(device_serial, "getprop ro.product.model")
    if ok:
        logger.info("[Device] Model: %s (%s)", out, device_serial)
    ok2, out2, _ = adb_shell(device_serial, "getprop ro.build.version.release")
    if ok2:
        logger.info("[Device] Android version: %s", out2)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG, format="[%(name)s] %(message)s")
    if len(sys.argv) < 3:
        print("Usage: python android_launcher.py <device_serial> <app_name>")
        print("Example: python android_launcher.py 192.168.1.7:5555 whatsapp")
        sys.exit(1)
    serial, app = sys.argv[1], " ".join(sys.argv[2:])
    success, message = adb_launch_app(serial, app)
    print(message)
    sys.exit(0 if success else 1)
