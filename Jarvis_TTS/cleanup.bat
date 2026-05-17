echo off
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe
timeout /t 2
rmdir /s /q K:\PROJECTS\Jarvis_TTS\output
echo CLEANED
pause