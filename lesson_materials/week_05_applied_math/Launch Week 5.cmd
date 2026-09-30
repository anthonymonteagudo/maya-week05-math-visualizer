@echo off
setlocal
set "WEEK05_TOOL_DIR=%~dp0"
start "" "C:\Program Files\Autodesk\Maya2027\bin\maya.exe" -script "%~dp0launch_week05.mel"
