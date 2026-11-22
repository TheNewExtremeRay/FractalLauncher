"""
FractalLauncher bootstrap — entry point for the PyInstaller .exe
Installs missing pip packages on first run, then launches the app
directly in the same process (no subprocess needed).
"""

import sys
import os
import subprocess
import datetime
import ctypes

# Detect frozen environment (works for cx_Freeze AND PyInstaller)
if getattr(sys, "frozen", False):
    # PyInstaller: sys._MEIPASS has the temp bundle dir (BASE_DIR)
    # but bundled jdk/ and Authlib/ live NEXT TO the exe (EXE_DIR),
    # so EXE_DIR must point at the executable's folder, not _MEIPASS.
    if hasattr(sys, "_MEIPASS"):
        BASE_DIR = sys._MEIPASS
        EXE_DIR = os.path.dirname(sys.executable)
    else:
        # cx_Freeze: executable lives in the install folder alongside launcher/
        BASE_DIR = os.path.dirname(sys.executable)
        EXE_DIR = BASE_DIR
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR  = BASE_DIR

# Make sure our launcher package is importable
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

REQUIRED_PACKAGES = [
    ("minecraft_launcher_lib",  "minecraft-launcher-lib"),
    ("PIL",                     "Pillow"),
    ("requests",                "requests"),
    ("cryptography",            "cryptography"),
]


def _title(msg):
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(f"FractalLauncher — {msg}")
    except Exception:
        pass


def _install_missing():
    # Skip in frozen PyInstaller (all packages bundled)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return
    
    missing = []
    for import_name, pip_name in REQUIRED_PACKAGES:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)

    if not missing:
        return

    _title(f"Installing {len(missing)} package(s)…")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade"] + missing,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


# ── Log file for diagnostics ────────────────────────────────────────────────
_LOG_FILE = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "launcher.log")


def _log(msg):
    """Write a diagnostic message to both stdout (if console exists) and the log file."""
    try:
        os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now():%H:%M:%S}] {msg}\n")
    except Exception:
        pass
    try:
        print(msg)
    except Exception:
        pass


def _check_webview2_runtime():
    """
    Check if the Microsoft Edge WebView2 Runtime is installed on this system.
    Returns (bool, str).
    """
    try:
        import winreg
        # Check both the per-machine and per-user install paths
        for hive, _label in [(winreg.HKEY_LOCAL_MACHINE, "HKLM"),
                            (winreg.HKEY_CURRENT_USER, "HKCU")]:
            try:
                key = winreg.OpenKey(hive,
                    r"Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}")
                try:
                    name, _ = winreg.QueryValueEx(key, "name")
                    if name:
                        return (True, name)
                finally:
                    winreg.CloseKey(key)
            except OSError:
                pass
        return (False, "WebView2 Runtime not found in registry.")
    except Exception as e:
        return (None, str(e))


def main():
    _title("Starting…")
    _install_missing()

    # Write first-run config (java/authlib auto-detect relative to exe folder)
    _setup_config()

    _title("Loading…")

    # Apply theme then launch
    import json
    config_path = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "config.json")

    def _apply_theme():
        theme_name = None
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    theme_name = json.load(f).get("theme")
            except Exception:
                pass

    # Use pywebview HTML UI
    ui_html = os.path.join(BASE_DIR, "assets", "ui.html")
    try:
        # ── Pre-flight checks ────────────────────────────────────────────────
        if not os.path.isfile(ui_html):
            raise FileNotFoundError(f"ui.html not found at {ui_html}")

        _log("[WebView] Importing pywebview...")
        import webview
        _log("[WebView] pywebview imported successfully")

        # Check WebView2 Runtime
        wv2_ok, wv2_msg = _check_webview2_runtime()
        if wv2_ok is False:
            _log(f"[WebView] WARNING: {wv2_msg}")
        elif wv2_ok is True:
            _log(f"[WebView] WebView2 Runtime detected: {wv2_msg}")
        else:
            _log(f"[WebView] Could not check WebView2 Runtime: {wv2_msg}")

        from launcher.profiles import ProfileManager
        from launcher.webview_bridge import API
        from launcher.window_icon import set_window_icon

        pm  = ProfileManager()
        api = API()
        icon_path = os.path.join(BASE_DIR, "assets", "logo.ico")

        _log("[WebView] Creating window...")
        window = webview.create_window(
            title="FractalLauncher v1.2.4 (Optimize Patch)",
            url=f"file:///{ui_html.replace(os.sep, '/')}",
            js_api=api,
            width=1200,
            height=720,
            min_size=(900, 580),
            background_color="#0d0f13",
        )

        def on_loaded():
            _log("[WebView] Window loaded - attaching API")
            api.attach(pm, window)
            if set_window_icon(window, icon_path):
                _log("[WebView] Window icon applied")

        window.events.loaded += on_loaded
        _log("[WebView] Starting event loop...")
        webview.start(debug=False)

    except FileNotFoundError as e:
        # ui.html is missing — log the full path so user can check the install
        _log(f"[WebView] CRITICAL: {e}")
        print(f"[WebView] CRITICAL: {e}")
        _apply_theme()
        from launcher.app import FractalLauncherApp
        app = FractalLauncherApp()
        app.mainloop()

    except ImportError as e:
        _log(f"[WebView] ImportError: {e}")
        print(f"[WebView] ImportError: {e}")
        # Try to auto-install pywebview (same logic as main.py)
        import subprocess as _sp
        print("[FractalLauncher] Installing pywebview...")
        try:
            _sp.run([sys.executable, "-m", "pip", "install", "--quiet", "pywebview"],
                    timeout=60, check=True)
            import webview as _wv
            from launcher.profiles import ProfileManager as _PM
            from launcher.webview_bridge import API as _API
            from launcher.window_icon import set_window_icon as _set_window_icon
            _pm = _PM(); _api = _API()
            _win = _wv.create_window("FractalLauncher v1.2.4 (Optimize Patch)",
                url=f"file:///{ui_html.replace(os.sep,'/')}",
                js_api=_api, width=1200, height=720,
                min_size=(900,580), background_color="#0d0f13")

            def _on_fallback_loaded():
                _api.attach(_pm, _win)
                _set_window_icon(_win, os.path.join(BASE_DIR, "assets", "logo.ico"))

            _win.events.loaded += _on_fallback_loaded
            _wv.start(debug=False)
        except Exception as install_err:
            _log(f"[WebView] Auto-install failed: {install_err}")
            print(f"[WebView] Auto-install failed: {install_err}")
            _apply_theme()
            from launcher.app import FractalLauncherApp
            FractalLauncherApp().mainloop()


    except Exception as e:
        # HTML UI failed and we have no fallback
        import traceback as _tb
        error_tb = _tb.format_exc()
        _log(f"[WebView] FAILED:\n{error_tb}")
        print(f"[WebView] FAILED:\n{error_tb}")
        print(f"ERROR: Could not start HTML UI: {e}")
        sys.exit(1)



def _setup_config():
    """Auto-detect bundled java/authlib relative to the .exe location."""
    import json

    config_dir  = os.path.join(os.path.expanduser("~"), ".FractalLauncher")
    config_path = os.path.join(config_dir, "config.json")
    os.makedirs(config_dir, exist_ok=True)

    existed = os.path.exists(config_path)
    cfg = {}
    if existed:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}

    changed = False

    # Fresh install (no config at all): mark as first launch so the
    # onboarding welcome/tour shows. Must be done here — this writer runs
    # BEFORE anything else on boot, so without it the flag never lands.
    if not existed and "first_launch" not in cfg and "firstLaunch" not in cfg:
        cfg["first_launch"] = True
        cfg["firstLaunch"] = True
        changed = True

    # Java — look in <exe_dir>/jdk/ (effective path is camelCase-first)
    java = cfg.get("javaPath") or cfg.get("java_path") or ""
    if not java or not os.path.isfile(java):
        jdk_root = os.path.join(EXE_DIR, "jdk")
        if os.path.isdir(jdk_root):
            for root, dirs, files in os.walk(jdk_root):
                for f in files:
                    if f.lower() == "javaw.exe":
                        found = os.path.join(root, f)
                        cfg["javaPath"] = found
                        cfg["java_path"] = found
                        changed = True
                        break
                if changed:
                    break

    # Authlib — look in <exe_dir>/Authlib/
    auth = cfg.get("authlibPath") or cfg.get("authlib_injector_path") or ""
    if not auth or not os.path.isfile(auth):
        authlib_dir = os.path.join(EXE_DIR, "Authlib")
        if os.path.isdir(authlib_dir):
            exact = os.path.join(authlib_dir, "Authlib.jar")
            if os.path.isfile(exact):
                cfg["authlibPath"] = exact
                cfg["authlib_injector_path"] = exact
                changed = True
            else:
                for f in os.listdir(authlib_dir):
                    if f.lower().endswith(".jar"):
                        found = os.path.join(authlib_dir, f)
                        cfg["authlibPath"] = found
                        cfg["authlib_injector_path"] = found
                        changed = True
                        break

    if "hideOnGame" not in cfg and "hide_launcher_on_game" not in cfg:
        cfg["hide_launcher_on_game"] = True
        changed = True

    if changed:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)


if __name__ == "__main__":
    main()
