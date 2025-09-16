@echo off
REM === Build NoteApp.exe (Windows) ===
REM Requirements: Python + pip + PyInstaller installed

REM Build using the spec file (includes tray_icon.png)
pyinstaller --clean app.spec

echo.
echo Build complete! EXE located in .\dist
