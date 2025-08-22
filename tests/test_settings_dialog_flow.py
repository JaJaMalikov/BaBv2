from __future__ import annotations

from PySide6.QtCore import QSettings

from ui.settings_dialog import SettingsDialog
from ui.settings_manager import SettingsManager


class _WinStub:
    """Minimal window stub for SettingsManager._apply_all_settings.
    We intentionally omit most attributes; the method guards or logs exceptions.
    """
    pass


def test_settings_dialog_apply_nonblocking_updates_qsettings(_app):
    # Use isolated QSettings scope
    org, app = "JaJaTest", "MacronotronSD"
    s = QSettings(org, app)
    # Ensure clean slate
    for key in [
        "ui/icon_dir",
        "ui/icon_size",
        "ui/theme",
        "timeline/bg",
    ]:
        s.remove(key)

    dlg = SettingsDialog(None)
    # Simulate user changes (no blocking; fixture patches exec globally)
    dlg.icon_dir_edit.setText("")
    dlg.icon_size_spin.setValue(36)
    dlg.preset_combo.setCurrentText("High Contrast")
    # Avoid scene background side effects by keeping it empty
    dlg.scene_bg_edit.setText("")

    sm = SettingsManager(_WinStub(), org=org, app=app)
    sm._apply_all_settings(dlg, s)

    # Assert QSettings updated with normalized values
    assert int(s.value("ui/icon_size", 0)) == 36
    assert str(s.value("ui/theme")).lower() == "high contrast"
