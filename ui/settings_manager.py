from __future__ import annotations

from typing import Any
from PySide6.QtCore import QSettings


class SettingsManager:
    """Encapsule l'enregistrement et la restauration des réglages UI (géométries, visibilité)."""

    def __init__(self, win: Any) -> None:
        self.win = win
        self.org = "JaJa"
        self.app = "Macronotron"

    def save(self) -> None:
        s = QSettings(self.org, self.app)
        s.setValue("geometry/mainwindow", self.win.saveGeometry())
        s.setValue("geometry/library", self.win.library_overlay.geometry())
        s.setValue("geometry/inspector", self.win.inspector_overlay.geometry())
        s.setValue("layout/timeline_visible", self.win.timeline_dock.isVisible())
        if hasattr(self.win.view, '_overlay') and self.win.view._overlay:
            s.setValue("geometry/view_toolbar", self.win.view._overlay.geometry())
        if hasattr(self.win.view, '_main_tools_overlay') and self.win.view._main_tools_overlay:
            s.setValue("geometry/main_toolbar", self.win.view._main_tools_overlay.geometry())

    def load(self) -> None:
        s = QSettings(self.org, self.app)
        if s.contains("geometry/mainwindow"):
            self.win.restoreGeometry(s.value("geometry/mainwindow"))
            self.win._settings_loaded = True
        if s.contains("geometry/library"):
            self.win.library_overlay.setGeometry(s.value("geometry/library"))
        self.win.set_library_overlay_visible(True)

        if s.contains("geometry/inspector"):
            self.win.inspector_overlay.setGeometry(s.value("geometry/inspector"))
        self.win.set_inspector_overlay_visible(True)
        if s.contains("layout/timeline_visible"):
            is_visible = s.value("layout/timeline_visible")
            # QSettings might return string 'true'/'false'
            self.win.timeline_dock.setVisible(is_visible in [True, 'true'])
        if hasattr(self.win.view, '_overlay') and self.win.view._overlay and s.contains("geometry/view_toolbar"):
            self.win.view._overlay.setGeometry(s.value("geometry/view_toolbar"))
        if hasattr(self.win.view, '_main_tools_overlay') and self.win.view._main_tools_overlay and s.contains("geometry/main_toolbar"):
            self.win.view._main_tools_overlay.setGeometry(s.value("geometry/main_toolbar"))

        # Ensure toolbars are always on top
        if hasattr(self.win.view, '_overlay') and self.win.view._overlay:
            self.win.view._overlay.raise_()
        if hasattr(self.win.view, '_main_tools_overlay') and self.win.view._main_tools_overlay:
            self.win.view._main_tools_overlay.raise_()

    def clear(self) -> None:
        s = QSettings(self.org, self.app)
        s.clear()

