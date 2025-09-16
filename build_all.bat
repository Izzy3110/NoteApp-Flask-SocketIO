@echo off

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
xcopy /y "backend-install_service.ps1" "dist\"
xcopy /y "backend-uninstall_service.ps1" "dist\"

robocopy tools dist\tools /MIR

echo.
echo Copy complete!

:: ========================
:: Ask user about service
:: ========================
echo.
echo "Do you want to install the backend as a Windows service now?"
choice /M "Install backend service"
if errorlevel 2 (
    echo Skipping service installation...
    echo.
    echo "Make sure to run the backend (NoteApp-backend.exe) first before starting the frontend (NoteApp.exe) app"
) else (
    echo.
    echo "Installing service..."
    cd dist

    powershell.exe -ExecutionPolicy Bypass -File "backend-uninstall_service.ps1"
    powershell.exe -ExecutionPolicy Bypass -File "backend-install_service.ps1"

    cd ..
    echo "Service installation finished!"
)

echo.
echo "Build process finished!"
pause
