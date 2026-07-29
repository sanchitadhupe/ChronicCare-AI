@echo off
title HealthGuard AI - Local Server
color 0A

REM ── Go to the folder containing this .bat file ──
cd /d "%~dp0"

echo.
echo  =============================================
echo    HealthGuard AI  ^|  Local Demo Server
echo  =============================================
echo.
echo  Working dir : %CD%
echo  Python      : %~dp0venv\Scripts\python.exe
echo.

REM ── Verify python exists ──
if not exist "%~dp0venv\Scripts\python.exe" (
    echo  [ERROR] venv\Scripts\python.exe not found!
    echo  Make sure you are running this from inside the
    echo  chronic_disease_monitor folder.
    pause
    exit /b 1
)

REM ── Start Flask ──
echo  [*] Starting server... open http://127.0.0.1:5000
echo  [*] AI responses can take 20-40 seconds - please wait after sending
echo  [*] Press Ctrl+C to stop.
echo.
"%~dp0venv\Scripts\python.exe" app.py

echo.
echo  [!] Server stopped.
pause
