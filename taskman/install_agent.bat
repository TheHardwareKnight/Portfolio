@echo off
:: install_agent.bat
:: Run this ONCE as Administrator to make agent.py start automatically on boot.

echo Installing Control Panel Agent...

:: Install Python dependencies
pip install psutil requests

:: Create a VBScript launcher that runs agent.py silently (no console window)
set AGENT_DIR=%~dp0
set VBS_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ctrl_agent.vbs

echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_PATH%"
echo WshShell.Run "pythonw ""%AGENT_DIR%agent.py""", 0, False >> "%VBS_PATH%"

echo.
echo Done! agent.py will start silently on next login.
echo To remove: delete %VBS_PATH%
echo To test now: python "%AGENT_DIR%agent.py"
pause
