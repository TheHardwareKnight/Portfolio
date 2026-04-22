@echo off
:: install.bat — Control Panel Agent Installer
:: Run as Administrator

title Control Panel Agent Installer

echo.
echo  ================================================
echo   CONTROL PANEL AGENT — INSTALLER
echo  ================================================
echo.

:: Check for admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Please right-click install.bat and run as Administrator.
    pause
    exit /b 1
)

:: Check Python
echo  [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Please install Python from https://python.org
    echo          Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
echo         OK

:: Install pip packages
echo  [2/5] Installing dependencies...
pip install psutil requests pyinstaller --quiet
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo         OK

:: Build silent exe with PyInstaller
echo  [3/5] Building executable (this may take a minute)...
pyinstaller --onefile --noconsole --name "ctrl-agent" agent.py --distpath "%~dp0dist" --workpath "%~dp0build" --specpath "%~dp0build" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to build executable.
    pause
    exit /b 1
)
echo         OK

:: Copy to ProgramData so it persists for all users
echo  [4/5] Installing agent...
set INSTALL_DIR=%ProgramData%\CtrlAgent
mkdir "%INSTALL_DIR%" >nul 2>&1
copy /y "%~dp0dist\ctrl-agent.exe" "%INSTALL_DIR%\ctrl-agent.exe" >nul

:: Add to all-users startup folder
set STARTUP=%ProgramData%\Microsoft\Windows\Start Menu\Programs\Startup
copy /y "%INSTALL_DIR%\ctrl-agent.exe" "%STARTUP%\ctrl-agent.exe" >nul
echo         OK

:: Run it now without waiting for reboot
echo  [5/5] Starting agent...
start "" /B "%INSTALL_DIR%\ctrl-agent.exe"
echo         OK

echo.
echo  ================================================
echo   Done! Agent is running and will auto-start
echo   on boot for all users.
echo.
echo   To uninstall, run uninstall.bat
echo  ================================================
echo.
pause
