@echo off
REM === Build NoteApp Backend EXE (Windows) ===
REM Requirements: Python + pip + PyInstaller installed

REM Build using PyInstaller
pyinstaller --onefile --noconsole ^
--name NoteApp-backend ^
--add-data "templates;templates" ^
--add-data "static;static" ^
--add-data "tray_icon-backend.png;." ^
--add-data "instance\NoteApp.db;instance" ^
--hidden-import engineio.async_drivers.threading ^
backend.py

echo.
echo Build complete! EXE located in .\dist
