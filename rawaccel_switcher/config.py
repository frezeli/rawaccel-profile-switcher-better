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
from dataclasses import asdict, dataclass
from pathlib import Path


APP_DIR_NAME = "RawAccelProfileSwitcher"


def app_data_dir() -> Path:
    """Return the per-user directory where config and profiles live."""
    base = os.environ.get("APPDATA")
    if base:
        root = Path(base) / APP_DIR_NAME
    else:
        root = Path.home() / f".{APP_DIR_NAME.lower()}"
    return root


@dataclass
class Config:
    """Persisted user settings."""

    rawaccel_dir: str = ""
    active_profile: str = ""

    # ----- locations -------------------------------------------------------
    @staticmethod
    def config_path() -> Path:
        return app_data_dir() / "config.json"

    @staticmethod
    def profiles_dir() -> Path:
        """Folder that holds the profile ``.json`` files."""
        return app_data_dir() / "profiles"

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
        self.profiles_dir().mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
