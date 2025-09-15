@echo off
REM === Build both executables ===

echo Building frontend...
call build_exe.bat

echo.
echo Building backend...
call build_exe-backend.bat

echo.
echo All builds complete!
pause
