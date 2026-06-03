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


# ----- config persistence --------------------------------------------------
def test_config_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    cfg = Config(rawaccel_dir=r"C:\RawAccel", active_profile="Gaming")
    cfg.save()

    loaded = Config.load()
    assert loaded.rawaccel_dir == r"C:\RawAccel"
    assert loaded.active_profile == "Gaming"


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


def test_current_settings_file(tmp_path):
    assert rawaccel.current_settings_file(tmp_path) is None
    (tmp_path / "settings.json").write_text("{}")
    assert rawaccel.current_settings_file(tmp_path) is not None
