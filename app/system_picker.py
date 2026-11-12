"""Native OS folder picker, opened by the local server process.

The browser cannot expose absolute filesystem paths, but montaz's server
is a native process on the user's machine — so it opens the real OS
folder dialog (tkinter, stdlib) and returns the chosen absolute path.
Only one picker may be open at a time.
"""
from __future__ import annotations

import threading

_lock = threading.Lock()


def try_lock() -> bool:
    """Non-blocking acquire: only one picker dialog at a time."""
    return _lock.acquire(blocking=False)


def release() -> None:
    if _lock.locked():
        _lock.release()


def pick_folder() -> str | None:
    """Open the native folder dialog; returns an absolute path or None on cancel."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:  # headless / stripped python builds
        raise RuntimeError("GUI dialog tidak tersedia di sistem ini.") from exc

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.lift()
    try:
        root.focus_force()
        path = filedialog.askdirectory(title="montaz — pilih folder project")
        return path or None
    except Exception:
        return None
    finally:
        root.destroy()
