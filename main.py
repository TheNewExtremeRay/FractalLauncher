"""
FractalLauncher - Entry point
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR  = os.path.join(os.path.expanduser("~"), ".FractalLauncher")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


def _find_bundled_java() -> str:
    """
    Searches the jdk/ folder next to main.py for javaw.exe at any depth.
    Works regardless of the exact JDK subfolder name.
    """
    jdk_root = os.path.join(BASE_DIR, "jdk")
    if os.path.isdir(jdk_root):
        for root, dirs, files in os.walk(jdk_root):
            for f in files:
                if f.lower() == "javaw.exe":
                    return os.path.join(root, f)
    return ""


def _find_bundled_authlib() -> str:
    """
    Looks for Authlib/Authlib.jar next to main.py.
    Falls back to any .jar in the Authlib folder if name differs.
    """
    authlib_dir = os.path.join(BASE_DIR, "Authlib")
    if not os.path.isdir(authlib_dir):
        return ""
    # Preferred exact name
    exact = os.path.join(authlib_dir, "Authlib.jar")
    if os.path.isfile(exact):
        return exact
    # Fallback: any jar in the folder
    for f in os.listdir(authlib_dir):
        if f.lower().endswith(".jar"):
            return os.path.join(authlib_dir, f)
    return ""


def _write_first_run_config():
    """
    On first run writes defaults pointing at bundled jdk/ and Authlib/.
    Only overwrites java_path / authlib_injector_path if they're missing
    or point to a file that no longer exists.
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)

    existed = os.path.exists(CONFIG_PATH)
    cfg = {}
    if existed:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}

    changed = False

    # Fresh install (no config at all): mark as first launch so the
    # onboarding welcome/tour shows.
    if not existed and "first_launch" not in cfg and "firstLaunch" not in cfg:
        cfg["first_launch"] = True
        cfg["firstLaunch"] = True
        changed = True

    java = cfg.get("javaPath") or cfg.get("java_path") or ""
    if not java or not os.path.isfile(java):
        found = _find_bundled_java()
        if found:
            cfg["javaPath"] = found
            cfg["java_path"] = found
            changed = True

    auth = cfg.get("authlibPath") or cfg.get("authlib_injector_path") or ""
    if not auth or not os.path.isfile(auth):
        found = _find_bundled_authlib()
        if found:
            cfg["authlibPath"] = found
            cfg["authlib_injector_path"] = found
            changed = True

    if "hideOnGame" not in cfg and "hide_launcher_on_game" not in cfg:
        cfg["hide_launcher_on_game"] = True
        changed = True

    if "font" not in cfg:
        cfg["font"] = "Inter"
        cfg["font_type"] = "preset"
        changed = True

    if changed:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)


def _apply_saved_theme():
    theme_name = None
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                theme_name = json.load(f).get("theme")
        except Exception:
            pass

    import launcher.theme as _theme
    from launcher.theme import THEMES, DEFAULT_THEME, _set_globals, _build_ctk_theme
    t = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    _set_globals(t)
    _theme.CTK_THEME = _build_ctk_theme(t)


_write_first_run_config()

if __name__ == "__main__":
    UI_HTML = os.path.join(BASE_DIR, "assets", "ui.html")
    try:
        import webview
        if not os.path.isfile(UI_HTML):
            raise FileNotFoundError(f"ui.html not found at {UI_HTML}")

        from launcher.profiles import ProfileManager
        from launcher.webview_bridge import API
        from launcher.window_icon import set_window_icon

        pm  = ProfileManager()
        api = API()
        icon_path = os.path.join(BASE_DIR, "assets", "logo.ico")

        window = webview.create_window(
            title="FractalLauncher v1.2.4 (Optimize Patch)",
            url=f"file:///{UI_HTML.replace(os.sep, '/')}",
            js_api=api,
            width=1200,
            height=720,
            min_size=(900, 580),
            background_color="#0d0f13",
        )

        def on_loaded():
            api.attach(pm, window)
            set_window_icon(window, icon_path)

        window.events.loaded += on_loaded
        webview.start(debug=False)

    except ImportError:
        # pywebview not installed — auto-install then retry, else fall back to CTK
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
                url=f"file:///{UI_HTML.replace(os.sep,'/')}",
                js_api=_api, width=1200, height=720,
                min_size=(900,580), background_color="#0d0f13")

            def _on_fallback_loaded():
                _api.attach(_pm, _win)
                _set_window_icon(_win, os.path.join(BASE_DIR, "assets", "logo.ico"))

            _win.events.loaded += _on_fallback_loaded
            _wv.start(debug=False)
        except Exception:
            _apply_saved_theme()
            from launcher.app import FractalLauncherApp
            FractalLauncherApp().mainloop()
    except Exception as e:
        print(f"[WebView] Failed: {e} — falling back to CustomTkinter UI")
        _apply_saved_theme()
        from launcher.app import FractalLauncherApp
        app = FractalLauncherApp()
        app.mainloop()
