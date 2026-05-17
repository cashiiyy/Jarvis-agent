# 🤖 JARVIS Voice Agent — Full Analysis & Execution Plan

## System Analysis Summary

| Component | Status | Detail |
|---|---|---|
| **GPU** | ✅ RTX 5050 | NVIDIA Driver 596.49, CUDA 13.2 |
| **PyTorch CUDA** | ✅ Working | torch + CUDA 12.8 — GPU accessible |
| **CTranslate2 (Whisper)** | ✅ GPU Ready | All float16/int8 types supported on CUDA |
| **faster-whisper** | ✅ Installed | Can run on GPU now |
| **pyaudio / sounddevice** | ✅ Working | Mic/speaker ready |
| **openwakeword** | ❌ BROKEN | numpy 2.x ↔ sklearn/pandas binary incompatibility |
| **Ollama (LLM)** | ❌ NOT RUNNING | ConnectionRefused on port 11434 |
| **ADB** | ⚠️ No devices | Daemon starts OK but no phone/tablet connected yet |
| **"on my laptop" routing** | ❌ MISSING | Router/orchestrator has no laptop-local path for voice commands |
| **Wake reply** | ⚠️ Wrong text | Says "Yes sir?" but requirement is "Yes Sir ..?" |
| **Whisper device** | ⚠️ CPU only | STT still hardcoded to CPU — should use GPU now that CT2 is GPU-capable |

---

## 🐛 Bugs Found

### Bug 1 — `openwakeword` crashes due to numpy 2.x
- **Location**: `JarvisAssistant/jarvis_voice/wake_word.py` (import-time crash via sklearn)
- **Root Cause**: `openwakeword` depends on `sklearn` and `pandas`, which were built for numpy 1.x. numpy 2.2.6 is installed.
- **Fix**: Pin `numpy<2.0` in the JarvisAssistant venv and reinstall affected packages.

### Bug 2 — "on my laptop" command does nothing
- **Location**: `voice_agent_hub/main_orchestrator.py` lines 208-222
- **Root Cause**: The routing block only checks for `"on my phone"` and `"on my tablet"`. A laptop command falls into the `else` branch which says *"Please specify which device"* — never executes locally.
- **Fix**: Add `"on my laptop"` / no-device-specified → execute via `subprocess` / `pyautogui` on the local machine.

### Bug 3 — `JarvisAssistant/main.py` — Tablet routing missing
- **Location**: `jarvis_network/router.py` line 24
- **Root Cause**: Only `phone` is handled for Android. `tablet` falls into the same `android_phone` object with phone's ADB serial — no separate tablet controller.
- **Fix**: `DeviceRouter` needs a separate `android_tablet` with the tablet's IP from `.env`.

### Bug 4 — Wake word reply text
- **Location**: `main_orchestrator.py` line 186
- **Root Cause**: Says `"Yes sir?"` but requirement says `"Yes Sir ..?"`
- **Fix**: Change the string.

### Bug 5 — STT runs on CPU despite GPU being available
- **Location**: `voice_agent_hub/main_orchestrator.py` line 68  
- **Root Cause**: Hardcoded `device="cpu"`. CTranslate2 now confirms GPU support.
- **Fix**: Auto-detect via `ctranslate2.get_supported_compute_types("cuda")`.

### Bug 6 — Ollama not running
- **Location**: System service
- **Root Cause**: Ollama server not started — intent parser will always return error fallback.
- **Fix**: Start Ollama + pull `llama3` model, or start it as a background process in the startup script.

### Bug 7 — `voice_agent_hub` has no laptop execution path
- **Location**: `voice_agent_hub/main_orchestrator.py`  
- **Root Cause**: "Open WhatsApp on my laptop" → no handler. Only phone/tablet via Open-AutoGLM.
- **Fix**: Add local Windows execution for laptop via `subprocess` + `pyautogui` (open app by name).

---

## ✅ Execution Plan (Step-by-Step)

### Phase 1 — Fix Dependencies
1. Fix numpy conflict — upgrade pandas/sklearn to numpy-2.x compatible versions.
2. Upgrade `faster-whisper` whisper model to use GPU (float16).
3. Ensure `ollama` is available and `llama3` is pulled.

### Phase 2 — Rewrite `voice_agent_hub/main_orchestrator.py`
- Load Whisper on **GPU** (via CTranslate2).
- Fix wake-word reply to `"Yes Sir ..?"`.
- Add `"on my laptop"` routing → local `subprocess`/`pyautogui` execution.
- Maintain `"on my phone"` → Mobile IP and `"on my tab"/"tablet"` → Tablet IP.

### Phase 3 — Fix `JarvisAssistant` multi-device router
- `DeviceRouter` reads `MOBILE_IP_PORT` and `TABLET_IP_PORT` from `.env`.
- Creates separate `android_phone` and `android_tablet` ADB controllers.
- Routes `target_device == "tablet"` to tablet controller.

### Phase 4 — Fix openwakeword numpy conflict
- Upgrade compatible packages in JarvisAssistant venv.

### Phase 5 — Add startup script
- One-click `start_jarvis.bat` that: starts Ollama, connects ADB devices, then runs the orchestrator.

### Phase 6 — Verification
- Dry-run test of all imports.
- Confirm `"Open WhatsApp on my laptop"` executes locally.
- Confirm `"Open WhatsApp on my phone"` routes to phone IP.
- Confirm `"Open WhatsApp on my TAB"` routes to tablet IP.
