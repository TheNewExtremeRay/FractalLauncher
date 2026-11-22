"""Apply the launcher icon to the native Windows window.

pywebview's ``webview.start(icon=...)`` option is ignored on Windows, and the
taskbar can keep showing a cached icon from an older executable. Setting
``WM_SETICON`` explicitly from the current ``assets/logo.ico`` avoids that.
"""

import ctypes
import os
import sys
from ctypes import wintypes

_ICON_HANDLES = []


def _window_handle(window):
    native = getattr(window, "native", None)
    handle = getattr(native, "Handle", None)
    if handle is not None:
        try:
            if hasattr(handle, "ToInt64"):
                return int(handle.ToInt64())
            return int(handle)
        except (TypeError, ValueError):
            pass

    title = getattr(window, "title", None)
    if not title:
        return 0
    try:
        return int(ctypes.windll.user32.FindWindowW(None, str(title)) or 0)
    except Exception:
        return 0


def set_window_icon(window, icon_path):
    """Set big/small window icons from *icon_path*. Returns True on success."""
    if sys.platform != "win32" or not os.path.isfile(icon_path):
        return False

    try:
        user32 = ctypes.windll.user32

        user32.LoadImageW.argtypes = [
            wintypes.HINSTANCE,
            wintypes.LPCWSTR,
            wintypes.UINT,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.SendMessageW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.SendMessageW.restype = wintypes.LPARAM

        hwnd = _window_handle(window)
        if not hwnd:
            return False

        image_icon = 1
        lr_loadfromfile = 0x0010
        lr_defaultsize = 0x0040
        wm_seticon = 0x0080
        icon_small = 0
        icon_big = 1
        icon_small2 = 2

        hicon = user32.LoadImageW(
            None,
            str(icon_path),
            image_icon,
            0,
            0,
            lr_loadfromfile | lr_defaultsize,
        )
        if not hicon:
            return False

        _ICON_HANDLES.append(hicon)
        for which in (icon_big, icon_small, icon_small2):
            user32.SendMessageW(hwnd, wm_seticon, which, hicon)
        return True
    except Exception:
        return False
