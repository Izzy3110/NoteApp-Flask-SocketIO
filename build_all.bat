@echo off
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

pause
