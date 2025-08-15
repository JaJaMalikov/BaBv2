"""Module for building and positioning side panels and overlays."""

from __future__ import annotations

import logging
from typing import Tuple

from pathlib import Path
from PySide6.QtWidgets import QVBoxLayout

from ui.draggable_widget import PanelOverlay, DraggableHeader
from ui.library.library_widget import LibraryWidget
from ui.inspector.inspector_widget import InspectorWidget


def build_side_overlays(win) -> Tuple[PanelOverlay, LibraryWidget, PanelOverlay, InspectorWidget]:
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


def position_overlays(win) -> None:
    """Position default Library/Inspector overlays and adjust tool overlays.

    Keeps behavior identical to previous inline implementation in MainWindow._position_overlays.
    """
    if getattr(win, "_settings_loaded", False):
        return

    win.set_library_overlay_visible(True)
    win.set_inspector_overlay_visible(True)

    margin = 10
    try:
        from PySide6.QtCore import QSettings
        s = QSettings("JaJa", "Macronotron")
        lib_size = s.value("ui/default/library_size")
        insp_size = s.value("ui/default/inspector_size")
        lib_pos = s.value("ui/default/library_pos")
        insp_pos = s.value("ui/default/inspector_pos")
        lib_w, lib_h = 290, 550
        insp_w, insp_h = 290, 550
        try:
            if lib_size:
                lib_w = int(lib_size.width()) if hasattr(lib_size, 'width') else int(lib_size[0])
                lib_h = int(lib_size.height()) if hasattr(lib_size, 'height') else int(lib_size[1])
            if insp_size:
                insp_w = int(insp_size.width()) if hasattr(insp_size, 'width') else int(insp_size[0])
                insp_h = int(insp_size.height()) if hasattr(insp_size, 'height') else int(insp_size[1])
        except (TypeError, ValueError, AttributeError):
            logging.exception("Failed to read default overlay sizes")
        if lib_pos and hasattr(lib_pos, 'x'):
            win.library_overlay.setGeometry(int(lib_pos.x()), int(lib_pos.y()), lib_w, lib_h)
        else:
            win.library_overlay.setGeometry(margin, margin, lib_w, lib_h)
        if insp_pos and hasattr(insp_pos, 'x'):
            win.inspector_overlay.setGeometry(int(insp_pos.x()), int(insp_pos.y()), insp_w, insp_h)
        else:
            win.inspector_overlay.setGeometry(win.width() - insp_w - margin, margin, insp_w, insp_h)

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
