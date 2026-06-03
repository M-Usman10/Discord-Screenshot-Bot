@echo off
echo Stopping Discord Screenshot Bot...

powershell -Command "Get-WmiObject Win32_Process | Where-Object { $_.Name -eq 'pythonw.exe' -and $_.CommandLine -like '*main.py*' } | ForEach-Object { Write-Host 'Killing PID' $_.ProcessId; Stop-Process -Id $_.ProcessId -Force }"

echo Done.
pause
