@echo off
setlocal
title FractalLauncher v1.2.4 (Optimize Patch) Build
echo ============================================
echo   FractalLauncher v1.2.4 (Optimize Patch) Build
echo ============================================
echo.

echo [1/2] Building EXE with PyInstaller...
echo.
python build_pyinstaller.py
if errorlevel 1 (
    echo ERROR: PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo [2/2] Building installer with NSIS...
echo.
python build_msi.py
if errorlevel 1 (
    echo ERROR: Installer build failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   BUILD COMPLETE
echo ============================================
echo.
pause
