"""Module for inspector-related actions."""

from __future__ import annotations

from typing import Any


def set_inspector_overlay_visible(win: Any, visible: bool) -> None:
    """Sets the visibility of the inspector overlay."""
    win.overlays.set_inspector_visible(visible)
    win.toggle_inspector_action.blockSignals(True)
    win.toggle_inspector_action.setChecked(visible)
    win.toggle_inspector_action.blockSignals(False)
