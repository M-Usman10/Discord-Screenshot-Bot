@echo off
cd /d "%~dp0"

:: Use venv python if it exists, otherwise fall back to system python
if exist "%~dp0discord-bot\Scripts\python.exe" (
    set PYTHON="%~dp0discord-bot\Scripts\python.exe"
) else if exist "%~dp0venv\Scripts\python.exe" (
    set PYTHON="%~dp0venv\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set PYTHON="%~dp0.venv\Scripts\python.exe"
) else (
    set PYTHON=python
)

echo Starting Discord Screenshot Bot...
echo Using: %PYTHON%
echo.

%PYTHON% main.py
pause
