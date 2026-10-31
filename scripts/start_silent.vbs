Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

strScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
strBatPath = FSO.BuildPath(strScriptDir, "start_dashboard.bat")

' Run start_dashboard.bat hidden (0 = hide window, false = do not wait)
WshShell.Run Chr(34) & strBatPath & Chr(34), 0, False
