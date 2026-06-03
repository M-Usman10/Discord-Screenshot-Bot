@echo off
echo Stopping Discord Screenshot Bot...

:: Find pythonw.exe processes running main.py from this folder and kill only those
for /f "tokens=2" %%i in ('wmic process where "name='pythonw.exe' and commandline like '%%main.py%%'" get processid /format:list ^| findstr "="') do (
    echo Killing PID %%i
    taskkill /f /pid %%i
)

echo Done.
pause
