from pathlib import Path
import json

from controllers.settings_service import SettingsService, SettingsSchema


def test_defaults_values():
    s = SettingsService.defaults()
    assert isinstance(s, SettingsSchema)
    assert s.theme == "dark"
    assert s.onion_opacity == 0.5
    assert s.onion_span == 2
    assert s.last_open_dir is None
    assert s.last_save_dir is None


def test_round_trip_json(tmp_path):
    s = SettingsService.defaults()
    s.last_open_dir = str(tmp_path)
    profile_path = tmp_path / "profile.json"

    SettingsService.save_json(profile_path, s)
    loaded, issues = SettingsService.load_json(profile_path)

    assert issues == []
    assert loaded.theme == s.theme
    assert loaded.onion_opacity == s.onion_opacity
    assert loaded.onion_span == s.onion_span
    assert loaded.last_open_dir == s.last_open_dir


def test_unknown_fields_and_version_namespace():
    profile = {
        "namespace": "other",
        "version": 0,
        "data": {
            "theme": "light",
            "foo": 123,  # unknown
        },
    }
    loaded, issues = SettingsService.from_profile_dict(profile)

    # Known field applied
    assert loaded.theme == "light"

    # Unknown field ignored (with info)
    assert any("ignored unknown field" in msg for msg in issues)

    # Namespace and version mismatch warnings present
    assert any("unexpected namespace" in msg for msg in issues)
    assert any("profile version" in msg for msg in issues)


def test_missing_file_returns_defaults(tmp_path):
    missing = tmp_path / "missing.json"
    loaded, issues = SettingsService.load_json(missing)
    assert isinstance(loaded, SettingsSchema)
    assert loaded == SettingsService.defaults()
    assert any("file not found" in msg for msg in issues)


def test_invalid_json_returns_defaults(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json }", encoding="utf-8")
    loaded, issues = SettingsService.load_json(bad)
    assert loaded == SettingsService.defaults()
    assert any("invalid JSON" in msg for msg in issues)


def test_key_namespacing_helper():
    assert SettingsService.key("ui", "theme") == "bab/ui/theme"
    assert SettingsService.key("/ui/", "/theme/") == "bab/ui/theme"
