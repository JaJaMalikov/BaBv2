from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings

from ui.ui_profile import UIProfile


def test_ui_profile_qsettings_roundtrip(tmp_path):
    # Use an isolated scope so we don't touch real settings
    org, app = "JaJaTest", "MacronotronRT"
    s = QSettings(org, app)
    # Start from a known profile and tweak some fields
    p = UIProfile.default_dark()
    p.icon_size = 44
    p.icon_color_normal = "#112233"
    p.icon_color_hover = "#445566"
    p.icon_color_active = "#778899"
    p.scene_bg = "#ABCDEF"
    p.menu_main_order = ["save", "load", "toggle_library"]
    p.menu_main_vis = {"save": True, "load": True, "toggle_library": False}
    p.timeline_inout_alpha = 123

    # Write to QSettings and read back
    p.apply_to_qsettings(s)
    p2 = UIProfile.from_qsettings(s)

    assert p2.icon_size == 44
    assert p2.icon_color_normal == "#112233"
    assert p2.icon_color_hover == "#445566"
    assert p2.icon_color_active == "#778899"
    assert p2.scene_bg == "#ABCDEF"
    assert p2.menu_main_order[:3] == ["save", "load", "toggle_library"]
    assert p2.menu_main_vis.get("toggle_library") is False
    assert p2.timeline_inout_alpha == 123


def test_ui_profile_json_roundtrip(tmp_path):
    p = UIProfile.default_dark()
    p.icon_size = 28
    p.menu_quick_order = ["zoom_in", "zoom_out", "fit"]
    p.menu_quick_vis = {"zoom_in": True, "zoom_out": True, "fit": True}
    out = Path(tmp_path) / "ui_profile.json"

    path = p.export_json(str(out))
    assert Path(path).exists()

    p2 = UIProfile.import_json(path)
    assert p2.icon_size == 28
    assert p2.menu_quick_order[:3] == ["zoom_in", "zoom_out", "fit"]
