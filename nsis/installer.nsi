
; FractalLauncher Installer Script
Icon "E:\\Projects - secret\\FractalLauncherOptimizable\\assets\\logo.ico"
!define MUI_ICON "E:\\Projects - secret\\FractalLauncherOptimizable\\assets\\logo.ico"
!define MUI_UNICON "E:\\Projects - secret\\FractalLauncherOptimizable\\assets\\logo.ico"
Name "FractalLauncher v1.2.4 (Optimize Patch)"
OutFile "E:\\Projects - secret\\FractalLauncherOptimizable\\nsis\FractalLauncher-1.2.4-Setup.exe"
InstallDir "$PROGRAMFILES\FractalLauncher"
InstallDirRegKey HKCU "Software\FractalLauncher" "Install_Dir"

; MUI Settings
!include "MUI2.nsh"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

; Installer sections
Section "Install"
  SetOutPath "$INSTDIR"
  
  ; Copy main EXE
  File "E:\\Projects - secret\\FractalLauncherOptimizable\\dist\\FractalLauncher.exe"

  ; Versioned shortcut icon avoids stale Windows icon-cache entries
  File /oname=FractalLauncher-1.2.4.ico "E:\\Projects - secret\\FractalLauncherOptimizable\\assets\\logo.ico"
  
  ; Copy JDK if exists
  IfFileExists "E:\\Projects - secret\\FractalLauncherOptimizable\\jdk\*.*" 0 SkipJDK
  SetOutPath "$INSTDIR\jdk"
  File /r "E:\\Projects - secret\\FractalLauncherOptimizable\\jdk\*.*"
  SkipJDK:
  
  ; Copy authlib if exists
  IfFileExists "E:\\Projects - secret\\FractalLauncherOptimizable\\authlib\*.*" 0 SkipAuthlib
  SetOutPath "$INSTDIR\authlib"
  File /r "E:\\Projects - secret\\FractalLauncherOptimizable\\authlib\*.*"
  SkipAuthlib:
  
  ; Copy assets if exists
  IfFileExists "E:\\Projects - secret\\FractalLauncherOptimizable\\assets\*.*" 0 SkipAssets
  SetOutPath "$INSTDIR\assets"
  File /r "E:\\Projects - secret\\FractalLauncherOptimizable\\assets\*.*"
  SkipAssets:
  
  ; Create shortcuts
  SetOutPath "$INSTDIR"
  CreateDirectory "$SMPROGRAMS\FractalLauncher"
  CreateShortcut "$SMPROGRAMS\FractalLauncher\FractalLauncher.lnk" "$INSTDIR\FractalLauncher.exe" "" "$INSTDIR\FractalLauncher-1.2.4.ico" 0
  CreateShortcut "$DESKTOP\FractalLauncher.lnk" "$INSTDIR\FractalLauncher.exe" "" "$INSTDIR\FractalLauncher-1.2.4.ico" 0
  System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, i 0, i 0)'

  ; Write registry
  WriteRegStr HKCU "Software\FractalLauncher" "Install_Dir" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FractalLauncher" "DisplayName" "FractalLauncher v1.2.4 (Optimize Patch)"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FractalLauncher" "DisplayIcon" "$INSTDIR\FractalLauncher.exe,0"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FractalLauncher" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; Uninstaller
Section "Uninstall"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\FractalLauncher"
  DeleteRegKey HKCU "Software\FractalLauncher"
  RMDir /r "$INSTDIR"
  RMDir /r "$SMPROGRAMS\FractalLauncher"
  Delete "$DESKTOP\FractalLauncher.lnk"
SectionEnd
