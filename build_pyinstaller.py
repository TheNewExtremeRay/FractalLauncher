#!/usr/bin/env python
"""
FractalLauncher build with PyInstaller (stable, handles pywebview)
"""
import os
import sys
import subprocess

APP_NAME = "FractalLauncher"
VERSION = "1.2.4"

def run(cmd):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def build():
    # Install PyInstaller if needed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    print(f"Building {APP_NAME} with PyInstaller...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "bootstrap.py",
        "-F",  # onefile
        "--windowed",  # no console
        "--name", APP_NAME,
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", ".",
        "--add-data", "assets:assets",
        # webview: only submodules + data files (js runtime, etc.) — the old
        # --collect-all also dragged in non-Windows platform data we never use.
        "--collect-submodules=webview",
        "--collect-data=webview",
        "--collect-all=PIL",
        "--collect-all=cryptography",
        "--collect-all=minecraft_launcher_lib",
        "--exclude-module=setuptools",
        "--exclude-module=pkg_resources",
        "--exclude-module=numpy",
        "--hidden-import=webview",
        "--hidden-import=webview.js",
        "--hidden-import=webview.platforms.winforms",
        "--hidden-import=minecraft_launcher_lib",
        "--hidden-import=PIL",
        "--hidden-import=cryptography",
        "--hidden-import=launcher",
        "--hidden-import=launcher.profiles",
        "--hidden-import=launcher.theme",
        "--hidden-import=launcher.webview_bridge",
        "--hidden-import=launcher.window_icon",
    ]
    
    # Add icon if exists
    if os.path.exists("assets/logo.ico"):
        cmd.extend(["-i", "assets/logo.ico"])
    
    cmd.append("-y")
    
    run(cmd)
    
    exe_path = f"dist/{APP_NAME}.exe"
    if os.path.exists(exe_path):
        print(f"\nOK Built successfully: {exe_path}")
        print(f"  Size: {os.path.getsize(exe_path) / 1024 / 1024:.1f} MB")
    else:
        print(f"\nFAIL Build failed - EXE not found at {exe_path}")
        sys.exit(1)

if __name__ == "__main__":
    build()
