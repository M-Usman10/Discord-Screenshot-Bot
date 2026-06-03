Dim fso, scriptDir, pythonExe
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Use venv pythonw if it exists, otherwise fall back to system pythonw
If fso.FileExists(scriptDir & "\discord-bot\Scripts\pythonw.exe") Then
    pythonExe = scriptDir & "\discord-bot\Scripts\pythonw.exe"
ElseIf fso.FileExists(scriptDir & "\venv\Scripts\pythonw.exe") Then
    pythonExe = scriptDir & "\venv\Scripts\pythonw.exe"
ElseIf fso.FileExists(scriptDir & "\.venv\Scripts\pythonw.exe") Then
    pythonExe = scriptDir & "\.venv\Scripts\pythonw.exe"
Else
    pythonExe = "pythonw.exe"
End If

CreateObject("WScript.Shell").Run """" & pythonExe & """ """ & scriptDir & "\main.py""", 0, False
