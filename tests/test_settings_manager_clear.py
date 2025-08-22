from __future__ import annotations

from PySide6.QtCore import QSettings

from ui.settings_manager import SettingsManager


def test_clear_removes_only_geometry_and_layout_keys():
    org, app = "JaJaTest", "MacronotronCLR"
    s = QSettings(org, app)

    # Seed geometry/layout keys and theme/icon/timeline keys
    s.setValue("geometry/mainwindow", b"bytesgeom")
    s.setValue("geometry/library", b"libgeom")
    s.setValue("geometry/inspector", b"inspgeom")
    s.setValue("geometry/view_toolbar", b"viewtb")
    s.setValue("geometry/main_toolbar", b"maintb")
    s.setValue("layout/timeline_visible", True)

    s.setValue("ui/theme", "dark")
    s.setValue("ui/icon_size", 40)
    s.setValue("ui/icon_color_normal", "#112233")
    s.setValue("timeline/bg", "#111111")

    # Sanity
    assert s.contains("geometry/mainwindow")
    assert s.contains("ui/theme")

    sm = SettingsManager(win=object(), org=org, app=app)
    sm.clear()

    # Geometry/layout removed
    for key in [
        "geometry/mainwindow",
        "geometry/library",
        "geometry/inspector",
        "geometry/view_toolbar",
        "geometry/main_toolbar",
        "layout/timeline_visible",
    ]:
        assert not s.contains(key), f"{key} should be removed"

    # Theme/icon/timeline preferences intact
    assert s.value("ui/theme") == "dark"
    assert int(s.value("ui/icon_size")) == 40
    assert s.value("ui/icon_color_normal") == "#112233"
    assert s.value("timeline/bg") == "#111111"
