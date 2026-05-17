@echo off
title JARVIS Voice Agent Hub
color 0A
echo ==============================================
echo          JARVIS STARTUP SEQUENCE
echo ==============================================

:: ── 1. Start Ollama (LLM backend) ──────────────────────────────────────
echo [1/4] Starting Ollama LLM server...
start "" ollama serve
timeout /t 3 /nobreak >nul

:: ── 2. Pull llama3 if not already available ─────────────────────────────
echo [2/4] Ensuring llama3 model is available...
ollama pull llama3 2>nul
echo      llama3 ready.

:: ── 3. Start ADB server ─────────────────────────────────────────────────
echo [3/4] Starting ADB server...
adb start-server

:: ── 4. Read device IPs from .env ────────────────────────────────────────
echo [4/4] Connecting to wireless devices...

:: Parse .env for device IPs
for /f "usebackq tokens=1,2 delims==" %%A in ("voice_agent_hub\.env") do (
    if "%%A"=="MOBILE_IP_PORT"  set MOBILE_IP=%%B
    if "%%A"=="TABLET_IP_PORT"  set TABLET_IP=%%B
)

if defined MOBILE_IP (
    echo Connecting to phone: %MOBILE_IP%
    adb connect %MOBILE_IP% 2>nul
)
if defined TABLET_IP (
    echo Connecting to tablet: %TABLET_IP%
    adb connect %TABLET_IP% 2>nul
)

echo.
adb devices
echo.

:: ── 5. Run the Jarvis Voice Hub ─────────────────────────────────────────
echo ==============================================
echo     Launching JARVIS — Say 'Hey Jarvis'!
echo ==============================================
cd /d "%~dp0"
python voice_agent_hub\main_orchestrator.py
pause
