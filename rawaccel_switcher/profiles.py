"""Profile slot management.

A "profile" is just a RawAccel settings ``.json`` file stored in the
profiles folder. This module handles creating, listing, renaming and
deleting those files. It contains no GUI code so it can be unit tested.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import List


# RawAccel ships a ``settings.json`` describing the current driver state.
# When a new profile is created we copy that file as a starting point; if it
# is not available we fall back to this minimal, driver-valid default
# (acceleration disabled / 1:1 sensitivity).
DEFAULT_SETTINGS = {
    "version": "1.6.1",
    "profiles": [
        {
            "name": "Default",
            "Sensitivity multiplier": 1.0,
            "Whole/combined accel (set false for 'by component' mode)": True,
        }
    ],
}

# Characters that are not allowed in a profile name (they would be unsafe or
# invalid as file names on Windows).
_INVALID_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class ProfileError(Exception):
    """Raised for invalid profile operations (bad name, duplicate, etc.)."""


def validate_name(name: str) -> str:
    """Return a cleaned profile name or raise :class:`ProfileError`."""
    name = (name or "").strip()
    if not name:
        raise ProfileError("Profile name cannot be empty.")
    if _INVALID_NAME.search(name):
        raise ProfileError(
            'Profile name contains invalid characters (< > : " / \\ | ? *).'
        )
    if len(name) > 64:
        raise ProfileError("Profile name is too long (max 64 characters).")
    return name


class ProfileManager:
    """Create, list, rename and delete profile ``.json`` files.

    ``profiles_dir`` may be ``None`` when the RawAccel directory has not been
    set yet; in that case listing returns nothing and any operation that
    needs the folder raises a clear :class:`ProfileError`.
    """

    def __init__(self, profiles_dir: Path | None):
        self.profiles_dir = Path(profiles_dir) if profiles_dir else None

    def _path(self, name: str) -> Path:
        if self.profiles_dir is None:
            raise ProfileError("Set your RawAccel directory first.")
        return self.profiles_dir / f"{name}.json"

    def ensure_dir(self) -> None:
        if self.profiles_dir is None:
            raise ProfileError("Set your RawAccel directory first.")
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def list_profiles(self) -> List[str]:
        """Return profile names sorted case-insensitively."""
        if self.profiles_dir is None or not self.profiles_dir.exists():
            return []
        names = [p.stem for p in self.profiles_dir.glob("*.json")]
        return sorted(names, key=str.lower)

    def exists(self, name: str) -> bool:
        return self.profiles_dir is not None and self._path(name).exists()

    def path_for(self, name: str) -> Path:
        """Return the file path for a profile, raising if it is missing."""
        path = self._path(name)
        if not path.exists():
            raise ProfileError(f"Profile '{name}' does not exist.")
        return path

    def create(self, name: str, template: Path | None = None) -> Path:
        """Create a new profile.

        If ``template`` points at an existing settings file its contents are
        copied; otherwise a minimal default settings file is written.
        """
        name = validate_name(name)
        self.ensure_dir()
        path = self._path(name)
        if path.exists():
            raise ProfileError(f"A profile named '{name}' already exists.")

        if template and Path(template).is_file():
            shutil.copyfile(template, path)
        else:
            path.write_text(json.dumps(DEFAULT_SETTINGS, indent=4), encoding="utf-8")
        return path

    def rename(self, old: str, new: str) -> Path:
        """Rename a profile, returning the new path."""
        new = validate_name(new)
        src = self.path_for(old)
        dst = self._path(new)
        if dst.exists() and dst != src:
            raise ProfileError(f"A profile named '{new}' already exists.")
        src.rename(dst)
        return dst

    def delete(self, name: str) -> None:
        """Delete a profile file."""
        self.path_for(name).unlink()
