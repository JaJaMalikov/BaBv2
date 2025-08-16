"""Module for library-related actions."""

from __future__ import annotations

from typing import Any

def set_library_overlay_visible(win: Any, visible: bool) -> None:
    """Sets the visibility of the library overlay."""
    win.overlays.set_library_visible(visible)
    win.toggle_library_action.blockSignals(True)
    win.toggle_library_action.setChecked(visible)
    win.toggle_library_action.blockSignals(False)
