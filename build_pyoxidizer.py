#!/usr/bin/env python
"""
Build with PyOxidizer - superior to PyInstaller/cx_Freeze
"""
import os
import sys
import subprocess

def run(cmd):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def install_pyoxidizer():
    try:
        import pyoxidizer
        print(f"PyOxidizer already installed")
    except ImportError:
        print("Installing PyOxidizer...")
        run([sys.executable, "-m", "pip", "install", "pyoxidizer"])

def build():
    print("Building FractalLauncher with PyOxidizer...\n")
    run(["pyoxidizer", "build", "--path", ".", "exe"])
    print("\nBuild complete!")
    print("Look in: build/ directory for output")

if __name__ == "__main__":
    install_pyoxidizer()
    build()
