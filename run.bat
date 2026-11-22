@echo off
title FractalLauncher
echo Starting FractalLauncher...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================
    echo  FractalLauncher exited with error code %ERRORLEVEL%
    echo  Please copy the error above and report it.
    echo ============================================================
    pause
)
