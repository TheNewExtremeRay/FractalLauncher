"""
build.py  -  Build FractalLauncher.exe and FractalLauncherSetup.msi

Strategy:
  - PyInstaller builds the .exe (fast, single file, no runtime overhead)
  - cx_Freeze bdist_msi wraps the pre-built .exe into an .msi installer
    by treating the exe as a data file, not a Python script.

Requirements:
  pip install pyinstaller cx_Freeze

Usage:
  python build.py
"""

import os, sys, shutil, subprocess, uuid

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DIST_DIR     = os.path.join(BASE_DIR, "dist")
BUILD_DIR    = os.path.join(BASE_DIR, "build_tmp")
APP_NAME     = "FractalLauncher"
APP_VER      = "1.2.4"
APP_DISPLAY_NAME = f"{APP_NAME} v{APP_VER} (Optimize Patch)"
MANUFACTURER = "FractalLauncher"
UPGRADE_CODE = "{B7C4E2A1-3F8D-4B9C-A0E5-12F3D6789ABC}"
SEP          = ";" if sys.platform == "win32" else ":"

def run(cmd):
    print("  >", " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"\nERROR: command failed (exit {r.returncode})")
        sys.exit(r.returncode)

def pip_install(*pkgs):
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", *pkgs], check=True)

# ---------------------------------------------------------------------------
# STEP 1  -  PyInstaller: build the real exe (fast, no frozen overhead)

def build_exe():
    print("\n" + "="*60)
    print("STEP 1  -  Building .exe (PyInstaller)")
    print("="*60)

    icon     = os.path.join(BASE_DIR, "assets", "logo.ico")
    launcher = os.path.join(BASE_DIR, "launcher")
    assets   = os.path.join(BASE_DIR, "assets")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--noconsole",
        "--name", APP_NAME,
        "--distpath", DIST_DIR,
        "--workpath", BUILD_DIR,
        "--clean", "--noconfirm",
        "--add-data", f"{launcher}{SEP}launcher",
        "--hidden-import", "webview",
        "--hidden-import", "webview.platforms.winforms",
        "--hidden-import", "launcher.window_icon",
    ]
    if os.path.isdir(assets):
        cmd += ["--add-data", f"{assets}{SEP}assets"]
    if os.path.isfile(icon):
        cmd += ["--icon", icon]
    cmd.append(os.path.join(BASE_DIR, "bootstrap.py"))
    run(cmd)

    exe = os.path.join(DIST_DIR, APP_NAME + ".exe")
    if not os.path.isfile(exe):
        print("ERROR: exe not found after build"); sys.exit(1)
    print(f"\n  OK: {exe}")
    return exe

# ---------------------------------------------------------------------------
# STEP 2  -  Assemble staging folder
#            The MSI installs: FractalLauncher.exe + Authlib/ + jdk/ + config/
#            launcher/ is already baked into the exe by PyInstaller.

def assemble_staging():
    print("\n" + "="*60)
    print("STEP 2  -  Assembling staging folder")
    print("="*60)

    staging = os.path.join(BUILD_DIR, "staging")
    if os.path.exists(staging):
        shutil.rmtree(staging)
    os.makedirs(staging)

    for name in ["Authlib", "config", "jdk"]:
        src = os.path.join(BASE_DIR, name)
        if not os.path.exists(src): continue
        dst = os.path.join(staging, name)
        shutil.copytree(src, dst) if os.path.isdir(src) else shutil.copy2(src, dst)
        print(f"  [{'dir' if os.path.isdir(src) else 'file'}]  {name}")

    # Bundle cloudflared.exe for free Cloudflare tunnels (offline skin support)
    cloudflared_src = os.path.join(BASE_DIR, "cloudflared.exe")
    if os.path.isfile(cloudflared_src):
        shutil.copy2(cloudflared_src, os.path.join(staging, "cloudflared.exe"))
        print("  [exe]  cloudflared.exe (bundled)")
    else:
        print("  [skip] cloudflared.exe not found — will auto-download on first launch")
        print("         Download from: https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe")

    shutil.copy2(os.path.join(DIST_DIR, APP_NAME + ".exe"), staging)
    print(f"  [exe]  {APP_NAME}.exe\n  Staging: {staging}")
    return staging

# ---------------------------------------------------------------------------
# STEP 3  -  cx_Freeze MSI
#            We pass the pre-built .exe as a plain DATA file using include_files,
#            and use a tiny stub script as the cx_Freeze "entry point" just to
#            satisfy its requirement — the stub is never actually run.

def build_msi(staging):
    print("\n" + "="*60)
    print("STEP 3  -  Building MSI (cx_Freeze)")
    print("="*60)

    import cx_Freeze
    ver_parts = [int(x) for x in cx_Freeze.__version__.split(".")[:2] if x.isdigit()]
    base = "gui" if tuple(ver_parts[:2]) >= (7, 0) else "Win32GUI"
    print(f"  cx_Freeze {cx_Freeze.__version__}, base='{base}'")

    icon      = os.path.join(BASE_DIR, "assets", "logo.ico")
    icon_path = icon if os.path.isfile(icon) else ""

    # Write a minimal stub that cx_Freeze can compile without errors.
    # It immediately runs the real FractalLauncher.exe alongside itself.
    stub_py = os.path.join(BUILD_DIR, "msi_stub.py")
    stub_exe = os.path.join(BUILD_DIR, "msi_stub_dist", APP_NAME + ".exe")
    with open(stub_py, "w") as f:
        f.write(
            "import os, sys, subprocess\n"
            "here = os.path.dirname(sys.executable)\n"
            f"exe = os.path.join(here, '{APP_NAME}.exe')\n"
            "if os.path.isfile(exe):\n"
            "    subprocess.Popen([exe])\n"
        )

    # Build the stub exe with cx_Freeze
    stub_lines = [
        "import sys, os",
        f"sys.path.insert(0, {repr(BASE_DIR)})",
        "from cx_Freeze import setup, Executable",
        "",
        # include_files: the real PyInstaller exe + extras
        f"include_files = {repr([(os.path.join(staging, n), n) for n in os.listdir(staging) if n != APP_NAME + '.exe'])}",
        # Also bring in the real exe as a plain file
        f"include_files.append(({repr(os.path.join(staging, APP_NAME + '.exe'))}, {repr(APP_NAME + '.exe')}))",
        "",
        f"exe = Executable(",
        f"    script={repr(stub_py)},",
        f"    base={repr(base)},",
        f"    icon={repr(icon_path)},",
        f"    target_name={repr('Launch' + APP_NAME + '.exe')},",
        f"    shortcut_name={repr(APP_NAME)},",
        f"    shortcut_dir='DesktopFolder',",
        f")",
        "",
        f"setup(",
        f"    name={repr(APP_DISPLAY_NAME)},",
        f"    version={repr(APP_VER)},",
        f"    author={repr(MANUFACTURER)},",
        f"    options={{",
        f"        'build_exe': {{",
        f"            'include_files': include_files,",
        f"            'build_exe': {repr(os.path.join(BUILD_DIR, 'msi_build'))},",
        f"        }},",
        f"        'bdist_msi': {{",
        f"            'upgrade_code': {repr(UPGRADE_CODE)},",
        f"            'add_to_path': False,",
        f"            # Per-user install — no admin rights required",
        f"            'initial_target_dir': r'[LocalAppDataFolder]\\{APP_NAME}',",
        f"            'install_icon': {repr(icon_path)},",
        f"            'all_users': False,",
        f"            'summary_data': {{",
        f"                'author': {repr(MANUFACTURER)},",
        f"                'comments': {repr(APP_DISPLAY_NAME + ' — No admin required')},",
        f"            }},",
        f"        }},",
        f"    }},",
        f"    executables=[exe],",
        f")",
    ]

    setup_py = os.path.join(BUILD_DIR, "setup_msi.py")
    with open(setup_py, "w", encoding="utf-8") as f:
        f.write("\n".join(stub_lines))

    os.makedirs(DIST_DIR, exist_ok=True)
    run([sys.executable, setup_py, "bdist_msi", "--dist-dir", DIST_DIR])

    msis = sorted(f for f in os.listdir(DIST_DIR) if f.lower().endswith(".msi"))
    if not msis:
        print("ERROR: no .msi produced"); sys.exit(1)
    msi = os.path.join(DIST_DIR, msis[-1])
    print(f"\n  OK: {msi}")
    return msi

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try: import PyInstaller
    except ImportError:
        print("Installing PyInstaller..."); pip_install("pyinstaller")

    try: import cx_Freeze
    except ImportError:
        print("Installing cx_Freeze..."); pip_install("cx_Freeze")

    os.makedirs(DIST_DIR,  exist_ok=True)
    os.makedirs(BUILD_DIR, exist_ok=True)

    exe     = build_exe()
    staging = assemble_staging()
    msi     = build_msi(staging)

    print("\n" + "="*60)
    print("ALL DONE")
    print(f"  EXE : {exe}")
    print(f"  MSI : {msi}")
    print("="*60)
