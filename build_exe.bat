@echo off
REM === Build NoteApp.exe (Windows) ===
REM Requirements: Python + pip + PyInstaller installed

REM Upgrade pip and install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

REM Build using the spec file (includes tray_icon.png)
pyinstaller --clean app.spec

echo.
echo Build complete! EXE located in .\dist
