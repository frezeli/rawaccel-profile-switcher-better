"""Application configuration.

Stores user settings (the RawAccel directory and the name of the active
profile) in a small JSON file inside the per-user application data folder.
On Windows that is ``%APPDATA%\\RawAccelProfileSwitcher``; on other
platforms a hidden folder in the user's home directory is used so the code
remains importable and testable everywhere.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


APP_DIR_NAME = "RawAccelProfileSwitcher"


def app_data_dir() -> Path:
    """Return the per-user directory where the config file lives."""
    base = os.environ.get("APPDATA")
    if base:
        root = Path(base) / APP_DIR_NAME
    else:
        root = Path.home() / f".{APP_DIR_NAME.lower()}"
    return root


def migrate_legacy_profiles(config: "Config") -> None:
    """Move profiles created by older versions into the new location.

    Early builds stored profiles under the app-data folder; they now live
    inside the RawAccel directory. Copy any old profiles across (without
    overwriting) so upgrading users keep their slots.
    """
    legacy = app_data_dir() / "profiles"
    target = config.profiles_dir()
    if target is None or not legacy.is_dir():
        return
    target.mkdir(parents=True, exist_ok=True)
    for src in legacy.glob("*.json"):
        dst = target / src.name
        if not dst.exists():
            shutil.copyfile(src, dst)


@dataclass
class Config:
    """Persisted user settings."""

    rawaccel_dir: str = ""
    active_profile: str = ""

    # ----- locations -------------------------------------------------------
    @staticmethod
    def config_path() -> Path:
        return app_data_dir() / "config.json"

    def profiles_dir(self) -> Path | None:
        """Folder that holds the profile ``.json`` files.

        Profiles live in a ``profiles`` subfolder of the RawAccel directory
        so everything stays together and ``writer.exe`` can read them from
        right next to itself. Returns ``None`` until the RawAccel directory
        has been set.
        """
        if not self.rawaccel_dir:
            return None
        return Path(self.rawaccel_dir) / "profiles"

    # ----- persistence -----------------------------------------------------
    @classmethod
    def load(cls) -> "Config":
        """Load config from disk, returning defaults if it does not exist."""
        path = cls.config_path()
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # Corrupt or unreadable config: fall back to defaults rather
            # than crashing on startup.
            return cls()
        known = {f: data.get(f) for f in ("rawaccel_dir", "active_profile") if f in data}
        return cls(**known)

    def save(self) -> None:
        """Write config to disk, creating folders as needed."""
        path = self.config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        profiles = self.profiles_dir()
        if profiles is not None:
            profiles.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
