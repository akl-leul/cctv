@echo off
title CCTV Face Detection System
echo Starting CCTV Face Detection System...
echo.

REM Check if executable exists
if not exist "CCTV_Face_Detection_System.exe" (
    echo Error: CCTV_Face_Detection_System.exe not found!
    echo Please run build_app.py first to create the executable.
    pause
    exit /b 1
)

REM Run the application
CCTV_Face_Detection_System.exe

REM If the application exits with error code, pause to see the error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%
    pause
)
