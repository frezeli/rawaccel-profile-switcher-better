"""Windows startup registration.

Adds or removes a ``HKCU\...\Run`` registry entry so the app launches when
the user logs in. Only works when running as a frozen PyInstaller exe — the
checkbox in the GUI is disabled when running from source.
"""

from __future__ import annotations

import sys
from pathlib import Path

_APP_KEY = "RawAccelProfileSwitcher"
_RUN_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def is_available() -> bool:
    """Return True when startup registration is supported.

    Requires both the ``winreg`` module (Windows only) and a frozen exe
    (so the registry value points at a real standalone executable).
    """
    if not getattr(sys, "frozen", False):
        return False
    try:
        import winreg  # noqa: F401
        return True
    except ImportError:
        return False


def is_registered() -> bool:
    if not is_available():
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_PATH) as key:
            winreg.QueryValueEx(key, _APP_KEY)
            return True
    except OSError:
        return False


def register() -> None:
    """Add the app to the Windows startup registry."""
    if not is_available():
        return
    import winreg
    exe = str(Path(sys.executable).resolve())
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _RUN_PATH, access=winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, _APP_KEY, 0, winreg.REG_SZ, exe)


def unregister() -> None:
    """Remove the app from the Windows startup registry."""
    if not is_available():
        return
    import winreg
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_PATH, access=winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, _APP_KEY)
    except OSError:
        pass
