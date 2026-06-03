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
# (acceleration disabled / 1:1 sensitivity). The shape mirrors RawAccel 1.7.x
# so ``writer.exe`` accepts it.
def _default_accel_params() -> dict:
    return {
        "mode": "noaccel",
        "Gain / Velocity": True,
        "inputOffset": 0.0,
        "outputOffset": 0.0,
        "acceleration": 0.005,
        "decayRate": 0.1,
        "gamma": 1.0,
        "motivity": 1.5,
        "exponentClassic": 2.0,
        "scale": 1.0,
        "exponentPower": 0.05,
        "limit": 1.5,
        "syncSpeed": 5.0,
        "smooth": 0.5,
        "Cap / Jump": {"x": 15.0, "y": 1.5},
        "Cap mode": "output",
        "data": [],
    }


DEFAULT_SETTINGS = {
    "version": "1.7.0",
    "defaultDeviceConfig": {
        "disable": False,
        "Use constant time interval based on polling rate": False,
        "DPI (normalizes input speed unit: counts/ms -> in/s)": 0,
        "Polling rate Hz (keep at 0 for automatic adjustment)": 0,
    },
    "profiles": [
        {
            "name": "default",
            "Stretches domain for horizontal vs vertical inputs": {"x": 1.0, "y": 1.0},
            "Stretches accel range for horizontal vs vertical inputs": {"x": 1.0, "y": 1.0},
            "Whole or horizontal accel parameters": _default_accel_params(),
            "Vertical accel parameters": _default_accel_params(),
            "Input speed calculation parameters": {
                "Whole/combined accel (set false for 'by component' mode)": True,
                "lpNorm": 2.0,
                "Time in ms after which an input is weighted at half its original value.": 0.0,
                "Time in ms after which scale is weighted at half its original value.": 0.0,
                "Time in ms after which an output is weighted at half its original value.": 0.0,
            },
            "Output DPI": 1000.0,
            "Y/X output DPI ratio (vertical sens multiplier)": 1.0,
            "L/R output DPI ratio (left sens multiplier)": 1.0,
            "U/D output DPI ratio (up sens multiplier)": 1.0,
            "Degrees of rotation": 0.0,
            "Degrees of angle snapping": 0.0,
            "Input Speed Cap": 0.0,
        }
    ],
    "devices": [],
}

# Characters that are not allowed in a profile name (they would be unsafe or
# invalid as file names on Windows).
_INVALID_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _format_value(value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".") or "0"
    return str(value)


def _is_one(value: object) -> bool:
    try:
        return float(value) == 1.0
    except (TypeError, ValueError):
        return False


def _first_profile(data: dict):
    """Return the profile object holding the per-profile settings."""
    if isinstance(data, dict):
        profiles = data.get("profiles")
        if isinstance(profiles, list) and profiles and isinstance(profiles[0], dict):
            return profiles[0]
        return data
    return None


def _accel_mode(profile: dict) -> str | None:
    """Return the whole/horizontal acceleration mode (e.g. 'noaccel')."""
    for key, value in profile.items():
        kl = str(key).lower()
        if "accel parameters" in kl and "vertical" not in kl and isinstance(value, dict):
            for mode_key, mode_val in value.items():
                if str(mode_key).lower() == "mode":
                    return str(mode_val)
    return None


def summarize_profile(data: dict) -> List[tuple]:
    """Return ``(label, value)`` pairs describing a RawAccel profile.

    Tuned for the RawAccel 1.7 ``settings.json`` layout (Output DPI, per-axis
    ratios, nested accel parameters) while still recognising the older
    ``Sensitivity multiplier`` key. Matching is by substring so it tolerates
    small wording differences between versions. Per-axis ratios are only shown
    when they differ from the 1:1 default, to keep the panel readable.
    """
    profile = _first_profile(data)
    if not isinstance(profile, dict):
        return []

    lowered = {str(k).lower(): v for k, v in profile.items()}

    def find(needle: str):
        for lk, v in lowered.items():
            if needle in lk and not isinstance(v, (dict, list)):
                return v
        return None

    summary: List[tuple] = []

    mode = _accel_mode(profile)
    if mode:
        summary.append(("Accel mode", mode))

    # Sensitivity: RawAccel 1.7 uses "Output DPI"; older builds used a
    # "Sensitivity multiplier". Match the exact DPI key so it isn't confused
    # with the per-axis "... output DPI ratio" entries.
    dpi = lowered.get("output dpi")
    if dpi is not None:
        summary.append(("Output DPI", _format_value(dpi)))
    else:
        sens = find("sensitivity multiplier")
        if sens is not None:
            summary.append(("Sensitivity", _format_value(sens)))

    yx = find("y/x")
    if yx is not None:
        summary.append(("Vertical (Y/X)", _format_value(yx)))

    lr = find("l/r")
    if lr is not None and not _is_one(lr):
        summary.append(("Left (L/R)", _format_value(lr)))

    ud = find("u/d")
    if ud is not None and not _is_one(ud):
        summary.append(("Up (U/D)", _format_value(ud)))

    rotation = find("degrees of rotation")
    if rotation is not None:
        summary.append(("Rotation", f"{_format_value(rotation)}°"))

    snapping = find("angle snapping")
    if snapping is not None:
        summary.append(("Angle snapping", f"{_format_value(snapping)}°"))

    cap = find("input speed cap")
    if cap is not None:
        summary.append(("Speed cap", _format_value(cap)))

    return summary


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

    def overwrite(self, name: str, template: Path | None) -> Path:
        """Replace an existing profile's contents with ``template``.

        Used by "Update" to re-snapshot the current RawAccel settings into an
        existing slot. Refuses to run (rather than wiping the slot) if the
        template is missing.
        """
        path = self.path_for(name)
        if not (template and Path(template).is_file()):
            raise ProfileError(
                "Could not find RawAccel's settings.json. "
                "Click Apply in RawAccel first."
            )
        shutil.copyfile(template, path)
        return path

    def delete(self, name: str) -> None:
        """Delete a profile file."""
        self.path_for(name).unlink()

    def read(self, name: str) -> dict:
        """Load and return a profile's JSON contents."""
        path = self.path_for(name)
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ProfileError(f"Could not read profile '{name}': {exc}") from exc
