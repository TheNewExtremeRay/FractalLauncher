# Building FractalLauncher v1.2.4 (Optimize Patch)

## Prerequisites
1. Python 3.8+ — https://python.org
2. pip install nuitka cx_Freeze

## Folder structure
```
FractalLauncher/
├── main.py / bootstrap.py / build.py
├── launcher/  assets/  jdk/  Authlib/
└── cloudflared.exe   ← OPTIONAL: bundle for instant skin support
                         https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
                         If missing, auto-downloads ~30MB on first launch.
```

## Build
```batch
cd FractalLauncher
python build.py                  # Nuitka (default, pywebview-friendly)
python build.py --pyinstaller    # PyInstaller (legacy fallback)
```

## Installer behaviour
- Per-user install (no admin required) → %LOCALAPPDATA%\FractalLauncher
- Installs for current user only — works on any Windows account
- Desktop + Start Menu shortcuts created for current user
- Cloudflare tunnel starts automatically every launch for multiplayer skin support
