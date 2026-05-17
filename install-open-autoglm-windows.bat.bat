@echo off
title Open-AutoGLM One-Click Installer (Windows)
color 0A

echo ============================================
echo   Open-AutoGLM One-Click Installer (Windows)
echo ============================================
echo.

REM ============================================
REM STEP 1: CHECK PYTHON
REM ============================================
echo [1/8] Checking Python installation...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ and restart.
    pause
    exit /b
)
echo [OK] Python detected.
echo.

REM ============================================
REM STEP 2: CHECK ADB
REM ============================================
echo [2/8] Checking ADB installation...
adb version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] ADB not found.
    echo Install Android Platform Tools and add to PATH.
    pause
    exit /b
)
echo [OK] ADB detected.
echo.

REM ============================================
REM STEP 3: CHECK DEVICE CONNECTION
REM ============================================
echo [3/8] Checking connected Android devices...
adb devices
echo.
echo Make sure:
echo  - USB Debugging is ENABLED on your phone
echo  - You tapped "Allow USB Debugging"
echo.
set /p DEVICE_CONFIRM=Is your device listed as "device"? (y/n):

IF /I NOT "%DEVICE_CONFIRM%"=="y" (
    echo [ERROR] Device not ready.
    echo Fix the connection and re-run this installer.
    pause
    exit /b
)
echo [OK] Device confirmed.
echo.

REM ============================================
REM STEP 4: INSTALL ADB KEYBOARD
REM ============================================
echo [4/8] ADB Keyboard setup
echo.
echo Download ADBKeyboard.apk from:
echo https://github.com/senzhk/ADBKeyBoard
echo.
set /p ADBK_PATH=Enter FULL path to ADBKeyboard.apk:
set ADBK_PATH=%ADBK_PATH:"=%

IF NOT EXIST "%ADBK_PATH%" (
    echo [ERROR] File not found:
    echo %ADBK_PATH%
    pause
    exit /b
)

echo Installing ADB Keyboard...
adb install "%ADBK_PATH%"
IF ERRORLEVEL 1 (
    echo [ERROR] Failed to install ADB Keyboard.
    pause
    exit /b
)

echo Enabling ADB Keyboard input method...
adb shell ime enable com.android.adbkeyboard/.AdbIME
IF ERRORLEVEL 1 (
    echo [ERROR] Failed to enable ADB Keyboard.
    echo Please enable it manually on your phone.
    pause
    exit /b
)

echo [OK] ADB Keyboard installed and enabled.
echo.

REM ============================================
REM STEP 5: CONFIRM INSTALLATION
REM ============================================
echo This installer will now:
echo  - Clone Open-AutoGLM
echo  - Create a virtual environment
echo  - Install all dependencies
echo.
set /p INSTALL_CONFIRM=Continue installation? (y/n):

IF /I NOT "%INSTALL_CONFIRM%"=="y" (
    echo [CANCELLED] Installation aborted by user.
    pause
    exit /b
)

echo.
echo [INFO] Starting Open-AutoGLM installation...
echo.

REM ============================================
REM STEP 6: CLONE REPOSITORY
REM ============================================
echo [5/8] Cloning Open-AutoGLM repository...
IF EXIST Open-AutoGLM (
    echo [INFO] Open-AutoGLM folder already exists. Skipping clone.
) ELSE (
    git clone https://github.com/zai-org/Open-AutoGLM.git
)

cd Open-AutoGLM

REM ============================================
REM STEP 7: CREATE VIRTUAL ENVIRONMENT
REM ============================================
echo [6/8] Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

REM ============================================
REM STEP 8: INSTALL DEPENDENCIES
REM ============================================
echo [7/8] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

REM ============================================
REM FINAL MESSAGE
REM ============================================
echo.
echo ============================================
echo [SUCCESS] INSTALLATION COMPLETE
echo ============================================
echo.
echo NEXT STEPS:
echo 1. Keep ADB Keyboard enabled on your phone
echo 2. Run:
echo.
echo   venv\Scripts\activate
echo   python main.py --list-apps
echo.
echo TRY A FIRST TASK:
echo   python main.py "Open Chrome browser"
echo.
echo Your phone is now ready for AI control.
echo.
pause
