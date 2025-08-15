"""OverlayManager: centralise la construction, le positionnement et la visibilité des overlays.

Cette façade encapsule les appels existants (panels, zoomable_view) pour alléger MainWindow
sans changer le comportement.
"""

from __future__ import annotations
import logging
from typing import Any

from . import panels

class OverlayManager:
    """Manages the creation, positioning, and visibility of overlays."""
    def __init__(self, win: Any) -> None:
        """Initializes the overlay manager.

        Args:
            win: The main window of the application.
        """
        self.win = win

    # Construction / Positionnement
    def build_overlays(self) -> None:
        """Create library and inspector overlays and widgets."""
        self.win.library_overlay, self.win.library_widget, self.win.inspector_overlay, self.win.inspector_widget = panels.build_side_overlays(self.win)

    def position_overlays(self) -> None:
        """Position overlays within the main window."""
        panels.position_overlays(self.win)

    # Visibilité
    def set_library_visible(self, visible: bool) -> None:
        """Show or hide the library overlay and update its action."""
        self.win.library_overlay.setVisible(visible)
        self.win.toggle_library_action.blockSignals(True)
        self.win.toggle_library_action.setChecked(visible)
        self.win.toggle_library_action.blockSignals(False)

    def set_inspector_visible(self, visible: bool) -> None:
        """Show or hide the inspector overlay and update its action."""
        self.win.inspector_overlay.setVisible(visible)
        self.win.toggle_inspector_action.blockSignals(True)
        self.win.toggle_inspector_action.setChecked(visible)
        self.win.toggle_inspector_action.blockSignals(False)

    def set_custom_visible(self, visible: bool) -> None:
        """Toggle the optional custom tools overlay if present."""
        overlay = getattr(self.win.view, '_custom_tools_overlay', None)
        if overlay is not None:
            overlay.setVisible(visible)
        self.win.toggle_custom_action.blockSignals(True)
        self.win.toggle_custom_action.setChecked(visible)
        self.win.toggle_custom_action.blockSignals(False)

    # Menus / icônes
    def apply_menu_settings(self) -> None:
        """Forward menu visibility settings to the view."""
        try:
            self.win.view.apply_menu_settings_main()
            self.win.view.apply_menu_settings_quick()
        except (RuntimeError, AttributeError):
            logging.exception("Failed to apply menu settings")

    def refresh_overlay_icons(self) -> None:
        """Refresh overlay icons according to current theme."""
        try:
            self.win.view.refresh_overlay_icons(self.win)
        except (RuntimeError, AttributeError):
            logging.exception("Failed to refresh overlay icons")

