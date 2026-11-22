#!/usr/bin/env python
"""
Build real Windows installer using NSIS
Requires: NSIS installed (https://nsis.sourceforge.io/Download)
"""
import os
import sys
import subprocess

APP_NAME = "FractalLauncher"
VERSION = "1.2.4"
DISPLAY_NAME = f"{APP_NAME} v{VERSION} (Optimize Patch)"
EXE_PATH = "dist/FractalLauncher.exe"

def run(cmd):
    subprocess.run(cmd, check=True)

def build_exe_first():
    if not os.path.exists(EXE_PATH):
        print("Building EXE...")
        run([sys.executable, "build_pyinstaller.py"])
    else:
        print(f"Using EXE: {EXE_PATH}")

def create_nsis_script():
    """Create NSIS installer script with correct paths"""
    os.makedirs("nsis", exist_ok=True)
    
    # Get absolute paths
    exe_abs = os.path.abspath(EXE_PATH).replace("\\", "\\\\")
    jdk_abs = os.path.abspath("jdk").replace("\\", "\\\\")
    authlib_abs = os.path.abspath("authlib").replace("\\", "\\\\")
    assets_abs = os.path.abspath("assets").replace("\\", "\\\\")
    logo_abs = os.path.abspath("assets/logo.ico").replace("\\", "\\\\")
    output_abs = os.path.abspath("nsis").replace("\\", "\\\\")
    
    nsi_script = f'''
; {APP_NAME} Installer Script
Icon "{logo_abs}"
!define MUI_ICON "{logo_abs}"
!define MUI_UNICON "{logo_abs}"
Name "{DISPLAY_NAME}"
OutFile "{output_abs}\\{APP_NAME}-{VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES\\{APP_NAME}"
InstallDirRegKey HKCU "Software\\{APP_NAME}" "Install_Dir"

; MUI Settings
!include "MUI2.nsh"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

; Installer sections
Section "Install"
  SetOutPath "$INSTDIR"
  
  ; Copy main EXE
  File "{exe_abs}"

  ; Versioned shortcut icon avoids stale Windows icon-cache entries
  File /oname={APP_NAME}-{VERSION}.ico "{logo_abs}"
  
  ; Copy JDK if exists
  IfFileExists "{jdk_abs}\\*.*" 0 SkipJDK
  SetOutPath "$INSTDIR\\jdk"
  File /r "{jdk_abs}\\*.*"
  SkipJDK:
  
  ; Copy authlib if exists
  IfFileExists "{authlib_abs}\\*.*" 0 SkipAuthlib
  SetOutPath "$INSTDIR\\authlib"
  File /r "{authlib_abs}\\*.*"
  SkipAuthlib:
  
  ; Copy assets if exists
  IfFileExists "{assets_abs}\\*.*" 0 SkipAssets
  SetOutPath "$INSTDIR\\assets"
  File /r "{assets_abs}\\*.*"
  SkipAssets:
  
  ; Create shortcuts
  SetOutPath "$INSTDIR"
  CreateDirectory "$SMPROGRAMS\\{APP_NAME}"
  CreateShortcut "$SMPROGRAMS\\{APP_NAME}\\{APP_NAME}.lnk" "$INSTDIR\\{APP_NAME}.exe" "" "$INSTDIR\\{APP_NAME}-{VERSION}.ico" 0
  CreateShortcut "$DESKTOP\\{APP_NAME}.lnk" "$INSTDIR\\{APP_NAME}.exe" "" "$INSTDIR\\{APP_NAME}-{VERSION}.ico" 0
  System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, i 0, i 0)'

  ; Write registry
  WriteRegStr HKCU "Software\\{APP_NAME}" "Install_Dir" "$INSTDIR"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "DisplayName" "{DISPLAY_NAME}"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "DisplayIcon" "$INSTDIR\\{APP_NAME}.exe,0"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
  WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

; Uninstaller
Section "Uninstall"
  DeleteRegKey HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}"
  DeleteRegKey HKCU "Software\\{APP_NAME}"
  RMDir /r "$INSTDIR"
  RMDir /r "$SMPROGRAMS\\{APP_NAME}"
  Delete "$DESKTOP\\{APP_NAME}.lnk"
SectionEnd
'''
    
    nsi_file = "nsis/installer.nsi"
    with open(nsi_file, "w") as f:
        f.write(nsi_script)
    
    return nsi_file

def build_with_nsis(nsi_file):
    """Build installer using NSIS makensis"""
    
    # Find makensis
    makensis_paths = [
        r"C:\Program Files\NSIS\makensis.exe",
        r"C:\Program Files (x86)\NSIS\makensis.exe",
    ]
    
    makensis = None
    for path in makensis_paths:
        if os.path.exists(path):
            makensis = path
            break
    
    if not makensis:
        print("\nERROR: NSIS not found!")
        print("Download: https://nsis.sourceforge.io/Download")
        sys.exit(1)
    
    nsi_abs = os.path.abspath(nsi_file)
    print(f"Building installer with NSIS...")
    run([makensis, nsi_abs])
    
    installer = f"nsis/{APP_NAME}-{VERSION}-Setup.exe"
    if os.path.exists(installer):
        size = os.path.getsize(installer) / 1024 / 1024
        print(f"\n[OK] Real installer created: {installer}")
        print(f"     Size: {size:.1f} MB")
        return installer
    else:
        print("Build failed - installer not found")
        sys.exit(1)

def main():
    print(f"Building {DISPLAY_NAME} Real Installer\n")
    build_exe_first()
    nsi = create_nsis_script()
    build_with_nsis(nsi)

if __name__ == "__main__":
    main()
