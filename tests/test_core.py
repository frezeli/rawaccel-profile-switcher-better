"""Tests for the GUI-free core (config, profiles, rawaccel helpers)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rawaccel_switcher import rawaccel  # noqa: E402
from rawaccel_switcher.config import Config  # noqa: E402
from rawaccel_switcher.profiles import (  # noqa: E402
    ProfileError,
    ProfileManager,
    summarize_profile,
    validate_name,
)


# ----- profile name validation --------------------------------------------
def test_validate_name_trims():
    assert validate_name("  Gaming  ") == "Gaming"


@pytest.mark.parametrize("bad", ["", "   ", "a/b", "a:b", 'a"b', "a*b", "a?b"])
def test_validate_name_rejects_invalid(bad):
    with pytest.raises(ProfileError):
        validate_name(bad)


# ----- profile manager -----------------------------------------------------
def test_create_list_rename_delete(tmp_path):
    mgr = ProfileManager(tmp_path / "profiles")

    mgr.create("Gaming")
    mgr.create("Desktop")
    assert mgr.list_profiles() == ["Desktop", "Gaming"]  # case-insensitive sort

    # The created file is valid JSON.
    data = json.loads(mgr.path_for("Gaming").read_text())
    assert "profiles" in data

    mgr.rename("Gaming", "FPS")
    assert mgr.list_profiles() == ["Desktop", "FPS"]
    assert not mgr.exists("Gaming")

    mgr.delete("Desktop")
    assert mgr.list_profiles() == ["FPS"]


def test_create_duplicate_rejected(tmp_path):
    mgr = ProfileManager(tmp_path / "profiles")
    mgr.create("Gaming")
    with pytest.raises(ProfileError):
        mgr.create("Gaming")


def test_create_from_template(tmp_path):
    template = tmp_path / "settings.json"
    template.write_text(json.dumps({"hello": "world"}))
    mgr = ProfileManager(tmp_path / "profiles")
    mgr.create("Copied", template=template)
    assert json.loads(mgr.path_for("Copied").read_text()) == {"hello": "world"}


def test_rename_onto_existing_rejected(tmp_path):
    mgr = ProfileManager(tmp_path / "profiles")
    mgr.create("A")
    mgr.create("B")
    with pytest.raises(ProfileError):
        mgr.rename("A", "B")


def test_path_for_missing_raises(tmp_path):
    mgr = ProfileManager(tmp_path / "profiles")
    with pytest.raises(ProfileError):
        mgr.path_for("nope")


def test_overwrite_requires_template(tmp_path):
    mgr = ProfileManager(tmp_path / "profiles")
    mgr.create("Gaming")
    # No template -> refuse rather than wipe the slot.
    with pytest.raises(ProfileError):
        mgr.overwrite("Gaming", None)
    # With a template, contents are replaced.
    template = tmp_path / "settings.json"
    template.write_text('{"new": 1}')
    mgr.overwrite("Gaming", template)
    assert json.loads(mgr.path_for("Gaming").read_text()) == {"new": 1}


def test_read_returns_json(tmp_path):
    mgr = ProfileManager(tmp_path / "profiles")
    mgr.create("Gaming")
    assert "profiles" in mgr.read("Gaming")


def test_summarize_profile_rawaccel_17():
    # Mirrors the real RawAccel 1.7.0 settings.json layout.
    data = {
        "version": "1.7.0",
        "profiles": [
            {
                "name": "default",
                "Whole or horizontal accel parameters": {"mode": "noaccel", "scale": 1.0},
                "Vertical accel parameters": {"mode": "natural"},
                "Output DPI": 1000.0,
                "Y/X output DPI ratio (vertical sens multiplier)": 1.0,
                "L/R output DPI ratio (left sens multiplier)": 1.0,
                "U/D output DPI ratio (up sens multiplier)": 1.5,
                "Degrees of rotation": 5.0,
                "Degrees of angle snapping": 0.0,
                "Input Speed Cap": 0.0,
            }
        ],
    }
    summary = dict(summarize_profile(data))
    assert summary["Accel mode"] == "noaccel"           # horizontal/whole, not vertical
    assert summary["Output DPI"] == "1000"               # exact key, not a ratio
    assert summary["Vertical (Y/X)"] == "1"
    assert summary["Rotation"] == "5°"
    assert summary["Angle snapping"] == "0°"
    assert summary["Speed cap"] == "0"
    # L/R is default (1.0) so it's hidden; U/D differs so it's shown.
    assert "Left (L/R)" not in summary
    assert summary["Up (U/D)"] == "1.5"


def test_summarize_profile_older_sensitivity_key():
    data = {"profiles": [{"name": "x", "Sensitivity multiplier": 1.25}]}
    assert dict(summarize_profile(data))["Sensitivity"] == "1.25"


def test_summarize_profile_handles_unknown_shape():
    assert summarize_profile({"unrelated": "value"}) == []
    assert summarize_profile([]) == []


def test_manager_without_dir_is_safe():
    # No RawAccel directory set yet: listing is empty, creating is rejected.
    mgr = ProfileManager(None)
    assert mgr.list_profiles() == []
    assert mgr.exists("x") is False
    with pytest.raises(ProfileError):
        mgr.create("x")


# ----- config persistence --------------------------------------------------
def test_config_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    cfg = Config(rawaccel_dir=r"C:\RawAccel", active_profile="Gaming")
    cfg.save()

    loaded = Config.load()
    assert loaded.rawaccel_dir == r"C:\RawAccel"
    assert loaded.active_profile == "Gaming"


def test_profiles_dir_lives_in_rawaccel_dir(tmp_path):
    assert Config(rawaccel_dir="").profiles_dir() is None
    cfg = Config(rawaccel_dir=str(tmp_path))
    assert cfg.profiles_dir() == tmp_path / "profiles"


def test_migrate_legacy_profiles(tmp_path, monkeypatch):
    from rawaccel_switcher.config import migrate_legacy_profiles

    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    legacy = tmp_path / "appdata" / "RawAccelProfileSwitcher" / "profiles"
    legacy.mkdir(parents=True)
    (legacy / "op18k.json").write_text('{"old": true}')

    rawaccel_dir = tmp_path / "RawAccel"
    rawaccel_dir.mkdir()
    cfg = Config(rawaccel_dir=str(rawaccel_dir))
    migrate_legacy_profiles(cfg)

    moved = cfg.profiles_dir() / "op18k.json"
    assert moved.read_text() == '{"old": true}'


def test_config_load_missing_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "does-not-exist"))
    cfg = Config.load()
    assert cfg.rawaccel_dir == ""
    assert cfg.active_profile == ""


def test_config_load_corrupt_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    path = Config.config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json{{{")
    cfg = Config.load()
    assert cfg.rawaccel_dir == ""


# ----- rawaccel helpers ----------------------------------------------------
def test_is_valid_rawaccel_dir(tmp_path):
    assert not rawaccel.is_valid_rawaccel_dir(tmp_path)
    assert not rawaccel.is_valid_rawaccel_dir("")
    (tmp_path / rawaccel.WRITER_EXE).write_text("")
    assert rawaccel.is_valid_rawaccel_dir(tmp_path)


def test_apply_profile_missing_writer(tmp_path):
    profile = tmp_path / "p.json"
    profile.write_text("{}")
    with pytest.raises(rawaccel.RawAccelError):
        rawaccel.apply_profile(tmp_path, profile)


def test_apply_profile_passes_path_to_writer(tmp_path, monkeypatch):
    # Create a fake writer.exe that exits 0.
    writer = tmp_path / rawaccel.WRITER_EXE
    writer.write_text("")
    profile = tmp_path / "Gaming.json"
    profile.write_text("{}")

    calls = {}

    import subprocess as sp

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        return sp.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(sp, "run", fake_run)

    rawaccel.apply_profile(tmp_path, profile)

    # writer.exe must be invoked with the profile's path as its argument.
    assert calls["cmd"] == [str(writer), str(profile)]


def test_current_settings_file(tmp_path):
    assert rawaccel.current_settings_file(tmp_path) is None
    (tmp_path / "settings.json").write_text("{}")
    assert rawaccel.current_settings_file(tmp_path) is not None
