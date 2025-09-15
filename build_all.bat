@echo off
:: Admin check
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

:: Make sure we're in the script folder
cd /d "%~dp0"

REM Upgrade pip and install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

REM === Build both executables ===

echo Building frontend...
call build_exe.bat

echo.
echo Building backend...
call build_exe-backend.bat

echo.
echo All builds complete!

echo.
echo Copying config...
xcopy /y ".env" "dist\"
xcopy /y "install_service.ps1" "dist\"
xcopy /y "uninstall_service.ps1" "dist\"

robocopy tools dist\tools /MIR

echo.
echo Copy complete!

echo.
echo Installing service...
cd dist

REM Execute the PowerShell install script with bypassed execution policy
powershell.exe -ExecutionPolicy Bypass -File "uninstall_service.ps1"

REM Execute the PowerShell install script with bypassed execution policy
powershell.exe -ExecutionPolicy Bypass -File "install_service.ps1"
cd ..

echo.
echo Build + service installation finished!
pause
