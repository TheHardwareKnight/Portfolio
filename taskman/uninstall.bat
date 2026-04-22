@echo off
:: uninstall.bat — Control Panel Agent Uninstaller
:: Run as Administrator

title Control Panel Agent Uninstaller

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Please right-click and run as Administrator.
    pause
    exit /b 1
)

echo  Stopping agent...
taskkill /f /im ctrl-agent.exe >nul 2>&1

echo  Removing from startup...
set STARTUP=%ProgramData%\Microsoft\Windows\Start Menu\Programs\Startup
del /f /q "%STARTUP%\ctrl-agent.exe" >nul 2>&1

echo  Removing files...
set INSTALL_DIR=%ProgramData%\CtrlAgent
rmdir /s /q "%INSTALL_DIR%" >nul 2>&1

echo.
echo  Done. Agent has been removed.
pause
