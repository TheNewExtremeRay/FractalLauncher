@echo off
setlocal EnableExtensions
title FractalLauncher v1.2.4 (Optimize Patch) - Reset

echo ============================================
echo    FractalLauncher v1.2.4 (Optimize Patch) - Factory Reset
echo ============================================
echo.
echo Resets the launcher to a fresh first-run state:
echo   * Settings
echo   * Profiles and accounts
echo   * Custom themes, API key, uploaded fonts
echo   * Skin cache and world backups
echo.
echo NOT touched: your Minecraft data (.minecraft saves, mods, worlds).
echo The old launcher data is moved to a backup folder, not deleted.
echo.

rem Close the launcher if running (it would lock files / rewrite configs)
taskkill /F /IM FractalLauncher.exe >nul 2>&1
if not errorlevel 1 (
    echo Closed the running FractalLauncher.
    ping -n 3 127.0.0.1 >nul
)

set "SRC=%USERPROFILE%\.FractalLauncher"

if not exist "%SRC%" (
    echo.
    echo Nothing to reset - no launcher data found at:
    echo   %SRC%
    echo The next start of FractalLauncher will be a first run.
    echo.
    if /i not "%~1"=="/nopause" pause
    exit /b 0
)

rem Timestamp for the backup folder name (locale-independent)
set "STAMP="
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss" 2^>nul') do set "STAMP=%%i"
if not defined STAMP set "STAMP=%RANDOM%"

set "DST=%SRC%_reset_backup_%STAMP%"
move "%SRC%" "%DST%" >nul

if exist "%DST%" (
    echo.
    echo Reset complete. The launcher will start fresh on next launch.
    echo.
    echo Old data was moved to:
    echo   %DST%
    echo Delete that folder if you do not need it.
) else (
    echo.
    echo WARNING: could not move the launcher data folder.
    echo Make sure FractalLauncher is fully closed and try again.
)
echo.
echo Note: per-profile game folders under .minecraft\FractalLauncher_profiles
echo are kept on purpose - they contain your mods, saves and worlds.
echo.
if /i not "%~1"=="/nopause" pause
exit /b 0
