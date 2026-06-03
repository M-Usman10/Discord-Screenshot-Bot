@echo off
cd /d "%~dp0"
echo Installing PyInstaller...
pip install pyinstaller

echo Building exe...
python -m PyInstaller --onefile --noconsole ^
    --name "ScreenshotBot" ^
    --add-binary "%~dp0config.json;." ^
    --hidden-import win32gui ^
    --hidden-import win32ui ^
    --hidden-import win32con ^
    --hidden-import win32api ^
    --hidden-import pywintypes ^
    --hidden-import discord ^
    --hidden-import discord.ext.commands ^
    --hidden-import aiohttp ^
    --hidden-import schedule ^
    --hidden-import requests ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --collect-all discord ^
    --collect-all aiohttp ^
    main.py

echo.
echo Done! Find ScreenshotBot.exe in the dist\ folder.
echo Copy ScreenshotBot.exe and config.json to the same folder and run.
pause
