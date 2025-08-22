"""Module for building and positioning side panels and overlays."""

from __future__ import annotations

import logging
from typing import Tuple, Optional

from pathlib import Path
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import QSettings, QRect
from ui.settings_keys import ORG, APP, UI_DEFAULT_SIZE, UI_DEFAULT_POS

from ui.draggable_widget import PanelOverlay, DraggableHeader
from ui.views.library.library_widget import LibraryWidget
from ui.views.inspector.inspector_widget import InspectorWidget


def build_side_overlays(
    win,
) -> Tuple[PanelOverlay, LibraryWidget, PanelOverlay, InspectorWidget]:
    """Builds Library and Inspector overlays attached to the view and returns them.

    Returns (library_overlay, library_widget, inspector_overlay, inspector_widget).
    """
    # Library overlay
    library_overlay = PanelOverlay(win.view)
    library_overlay.setVisible(False)
    lib_layout = QVBoxLayout(library_overlay)
    lib_layout.setContentsMargins(8, 8, 8, 8)
    lib_layout.setSpacing(0)

    lib_drag_handle = DraggableHeader(library_overlay, parent=library_overlay)
    lib_drag_handle.setFixedHeight(20)
    lib_layout.addWidget(lib_drag_handle)

    library_widget = LibraryWidget(root_dir=str(Path.cwd()), parent=library_overlay)
    lib_layout.addWidget(library_widget)
    library_overlay.resize(360, 520)
    library_overlay.move(10, 100)

    # Inspector overlay
    inspector_overlay = PanelOverlay(win.view)
    inspector_overlay.setVisible(False)
    insp_layout = QVBoxLayout(inspector_overlay)
    insp_layout.setContentsMargins(8, 8, 8, 8)
    insp_layout.setSpacing(0)

    insp_drag_handle = DraggableHeader(inspector_overlay, parent=inspector_overlay)
    insp_drag_handle.setFixedHeight(20)
    insp_layout.addWidget(insp_drag_handle)

    inspector_widget = InspectorWidget(win)
    insp_layout.addWidget(inspector_widget)
    inspector_overlay.resize(380, 560)
    inspector_overlay.move(400, 100)

    return library_overlay, library_widget, inspector_overlay, inspector_widget


def _get_overlay_geometry(s: QSettings, name: str) -> Optional[QRect]:
    """Get overlay geometry from settings."""
    size_val = s.value(UI_DEFAULT_SIZE(name))
    pos_val = s.value(UI_DEFAULT_POS(name))

    w, h = 290, 550
    if size_val:
        try:
            w = (
                int(size_val.width())
                if hasattr(size_val, "width")
                else int(size_val[0])
            )
            h = (
                int(size_val.height())
                if hasattr(size_val, "height")
                else int(size_val[1])
            )
        except (TypeError, ValueError, AttributeError):
            pass

    if pos_val and hasattr(pos_val, "x"):
        return QRect(int(pos_val.x()), int(pos_val.y()), w, h)

    return None


def position_overlays(win) -> None:
    """Position default Library/Inspector overlays and adjust tool overlays."""
    if getattr(win, "_settings_loaded", False):
        return

    win.set_library_overlay_visible(True)
    win.set_inspector_overlay_visible(True)

    margin = 10
    try:
        s = QSettings(ORG, APP)
        lib_geom = _get_overlay_geometry(s, "library")
        insp_geom = _get_overlay_geometry(s, "inspector")

        if lib_geom:
            win.library_overlay.setGeometry(lib_geom)
        else:
            win.library_overlay.setGeometry(margin, margin, 290, 550)

        if insp_geom:
            win.inspector_overlay.setGeometry(insp_geom)
        else:
            win.inspector_overlay.setGeometry(
                win.width() - 290 - margin, margin, 290, 550
            )

        left_bound = win.library_overlay.geometry().right() + margin
        right_bound = win.inspector_overlay.geometry().left() - margin

        ov = getattr(win.view, "_overlay", None)
        mov = getattr(win.view, "_main_tools_overlay", None)

        if ov:
            ov.adjustSize()
            ov.move(left_bound, margin)
            ov.raise_()
        if mov:
            mov.adjustSize()
            mov.move(max(left_bound, right_bound - mov.width()), margin)
            mov.raise_()
    except RuntimeError as e:
        logging.debug("Overlay positioning skipped: %s", e)
