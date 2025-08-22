from __future__ import annotations

"""Geometry persistence helpers for SettingsManager."""

import logging
from typing import Any

from PySide6.QtCore import QSettings

from ui.ui_profile import _bool


def save(win: Any, org: str = "JaJa", app: str = "Macronotron") -> None:
    """Persist window and overlay geometries."""
    from ui.settings_keys import (
        GEOMETRY_MAINWINDOW,
        GEOMETRY_LIBRARY,
        GEOMETRY_INSPECTOR,
        GEOMETRY_VIEW_TOOLBAR,
        GEOMETRY_MAIN_TOOLBAR,
        LAYOUT_TIMELINE_VISIBLE,
    )

    s = QSettings(org, app)
    s.setValue(GEOMETRY_MAINWINDOW, win.saveGeometry())
    s.setValue(GEOMETRY_LIBRARY, win.library_overlay.geometry())
    s.setValue(GEOMETRY_INSPECTOR, win.inspector_overlay.geometry())
    s.setValue(LAYOUT_TIMELINE_VISIBLE, win.timeline_dock.isVisible())
    if hasattr(win.view, "_overlay") and win.view._overlay:
        s.setValue(GEOMETRY_VIEW_TOOLBAR, win.view._overlay.geometry())
    if hasattr(win.view, "_main_tools_overlay") and win.view._main_tools_overlay:
        s.setValue(GEOMETRY_MAIN_TOOLBAR, win.view._main_tools_overlay.geometry())


def load(win: Any, org: str = "JaJa", app: str = "Macronotron") -> None:
    """Restore window and overlay geometries."""
    s = QSettings(org, app)
    from ui.settings_keys import (
        GEOMETRY_MAINWINDOW,
        GEOMETRY_LIBRARY,
        GEOMETRY_INSPECTOR,
        GEOMETRY_VIEW_TOOLBAR,
        GEOMETRY_MAIN_TOOLBAR,
        LAYOUT_TIMELINE_VISIBLE,
    )

    has_any_geometry = (
        s.contains(GEOMETRY_MAINWINDOW)
        or s.contains(GEOMETRY_LIBRARY)
        or s.contains(GEOMETRY_INSPECTOR)
        or s.contains(GEOMETRY_VIEW_TOOLBAR)
        or s.contains(GEOMETRY_MAIN_TOOLBAR)
    )
    if s.contains(GEOMETRY_MAINWINDOW):
        win.restoreGeometry(s.value(GEOMETRY_MAINWINDOW))
    if has_any_geometry:
        win._settings_loaded = True
    if s.contains(GEOMETRY_LIBRARY):
        win.library_overlay.setGeometry(s.value(GEOMETRY_LIBRARY))
    win.set_library_overlay_visible(True)

    if s.contains(GEOMETRY_INSPECTOR):
        win.inspector_overlay.setGeometry(s.value(GEOMETRY_INSPECTOR))
    win.set_inspector_overlay_visible(True)
    try:
        win.library_overlay.raise_()
        win.inspector_overlay.raise_()
    except (RuntimeError, AttributeError):
        logging.debug("Failed to raise side overlays after load")
    if s.contains(LAYOUT_TIMELINE_VISIBLE):
        is_visible = _bool(s.value(LAYOUT_TIMELINE_VISIBLE), True)
        win.timeline_dock.setVisible(is_visible)
    if hasattr(win.view, "_overlay") and win.view._overlay and s.contains(GEOMETRY_VIEW_TOOLBAR):
        win.view._overlay.setGeometry(s.value(GEOMETRY_VIEW_TOOLBAR))
    if (
        hasattr(win.view, "_main_tools_overlay")
        and win.view._main_tools_overlay
        and s.contains(GEOMETRY_MAIN_TOOLBAR)
    ):
        win.view._main_tools_overlay.setGeometry(s.value(GEOMETRY_MAIN_TOOLBAR))

    if hasattr(win.view, "_overlay") and win.view._overlay:
        win.view._overlay.raise_()
    if hasattr(win.view, "_main_tools_overlay") and win.view._main_tools_overlay:
        win.view._main_tools_overlay.raise_()


def clear(org: str = "JaJa", app: str = "Macronotron") -> None:
    """Clear persisted geometry/layout keys without affecting theme or icons."""
    s = QSettings(org, app)
    from ui.settings_keys import (
        GEOMETRY_MAINWINDOW,
        GEOMETRY_LIBRARY,
        GEOMETRY_INSPECTOR,
        GEOMETRY_VIEW_TOOLBAR,
        GEOMETRY_MAIN_TOOLBAR,
        LAYOUT_TIMELINE_VISIBLE,
    )

    for key in [
        GEOMETRY_MAINWINDOW,
        GEOMETRY_LIBRARY,
        GEOMETRY_INSPECTOR,
        GEOMETRY_VIEW_TOOLBAR,
        GEOMETRY_MAIN_TOOLBAR,
        LAYOUT_TIMELINE_VISIBLE,
    ]:
        s.remove(key)
