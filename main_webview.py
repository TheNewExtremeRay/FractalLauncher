"""
main_webview.py — FractalLauncher with pywebview HTML UI
Run: python main_webview.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR  = os.path.join(os.path.expanduser("~"), ".FractalLauncher")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
UI_HTML     = os.path.join(BASE_DIR, "assets", "ui.html")


def _find_bundled_java() -> str:
    jdk_root = os.path.join(BASE_DIR, "jdk")
    if os.path.isdir(jdk_root):
        for root, dirs, files in os.walk(jdk_root):
            for f in files:
                if f.lower() == "javaw.exe":
                    return os.path.join(root, f)
    return ""


def _find_bundled_authlib() -> str:
    authlib_dir = os.path.join(BASE_DIR, "Authlib")
    if not os.path.isdir(authlib_dir):
        return ""
    exact = os.path.join(authlib_dir, "Authlib.jar")
    if os.path.isfile(exact):
        return exact
    for f in os.listdir(authlib_dir):
        if f.lower().endswith(".jar"):
            return os.path.join(authlib_dir, f)
    return ""


def _write_first_run_config():
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
    if not existed:
        cfg["first_launch"] = True
        changed = True
    if not cfg.get("java_path") or not os.path.isfile(cfg["java_path"]):
        java = _find_bundled_java()
        if java:
            cfg["java_path"] = java
            changed = True
    if not cfg.get("authlib_injector_path") or \
       not os.path.isfile(cfg["authlib_injector_path"]):
        authlib = _find_bundled_authlib()
        if authlib:
            cfg["authlib_injector_path"] = authlib
            changed = True
    if "hide_launcher_on_game" not in cfg:
        cfg["hide_launcher_on_game"] = True
        changed = True
    if "font" not in cfg:
        cfg["font"] = "Inter"
        cfg["font_type"] = "preset"
        changed = True
    if changed:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)


if __name__ == "__main__":
    _write_first_run_config()

    try:
        import webview
    except ImportError:
        print("pywebview not installed. Run: pip install pywebview")
        sys.exit(1)

    from launcher.profiles import ProfileManager
    from launcher.webview_bridge import API
    from launcher.window_icon import set_window_icon

    pm  = ProfileManager()
    api = API()
    icon_path = os.path.join(BASE_DIR, "assets", "logo.ico")

    if not os.path.isfile(UI_HTML):
        print(f"ERROR: UI file not found at {UI_HTML}")
        sys.exit(1)

    window = webview.create_window(
        title="FractalLauncher v1.2.4 (Optimize Patch)",
        url=f"file:///{UI_HTML.replace(os.sep, '/')}",
        js_api=api,
        width=1200,
        height=720,
        min_size=(900, 580),
        background_color="#0d0f13",
        frameless=False,
        easy_drag=False,
    )

    def on_loaded():
        api.attach(pm, window)
        set_window_icon(window, icon_path)

    window.events.loaded += on_loaded
    webview.start(debug=False)
