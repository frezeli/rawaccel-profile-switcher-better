"""Integration with the RawAccel ``writer.exe`` tool.

``writer.exe`` takes the path to a settings ``.json`` file as its only
argument and applies it to the RawAccel driver. Switching a profile
therefore means running ``writer.exe <path-to-profile.json>``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


WRITER_EXE = "writer.exe"


class RawAccelError(Exception):
    """Raised when RawAccel cannot be found or ``writer.exe`` fails."""


def writer_path(rawaccel_dir: str | Path) -> Path:
    """Return the path to ``writer.exe`` inside the RawAccel directory."""
    return Path(rawaccel_dir) / WRITER_EXE


def is_valid_rawaccel_dir(rawaccel_dir: str | Path) -> bool:
    """Return True if the directory looks like a RawAccel install."""
    if not rawaccel_dir:
        return False
    return writer_path(rawaccel_dir).is_file()


def current_settings_file(rawaccel_dir: str | Path) -> Path | None:
    """Return RawAccel's bundled ``settings.json`` if present.

    Used as a template when creating a new profile so the new slot starts
    from the user's current driver settings.
    """
    candidate = Path(rawaccel_dir) / "settings.json"
    return candidate if candidate.is_file() else None


def apply_profile(rawaccel_dir: str | Path, profile_path: str | Path) -> None:
    """Apply a profile to the driver by running ``writer.exe <profile>``.

    Raises :class:`RawAccelError` if the tooling is missing or the writer
    exits with a non-zero status.
    """
    rawaccel_dir = Path(rawaccel_dir)
    writer = writer_path(rawaccel_dir)
    if not writer.is_file():
        raise RawAccelError(
            f"Could not find {WRITER_EXE} in '{rawaccel_dir}'. "
            "Set the correct RawAccel directory first."
        )

    profile_path = Path(profile_path)
    if not profile_path.is_file():
        raise RawAccelError(f"Profile file not found: {profile_path}")

    try:
        result = subprocess.run(
            [str(writer), str(profile_path)],
            cwd=str(rawaccel_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except OSError as exc:
        raise RawAccelError(f"Failed to launch {WRITER_EXE}: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RawAccelError(f"{WRITER_EXE} timed out while applying the profile.") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        message = f"{WRITER_EXE} failed (exit code {result.returncode})."
        if detail:
            message += f"\n{detail}"
        raise RawAccelError(message)
