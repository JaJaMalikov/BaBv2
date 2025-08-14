from __future__ import annotations

"""OverlayManager: centralise la construction, le positionnement et la visibilité des overlays.

Cette façade encapsule les appels existants (panels, zoomable_view) pour alléger MainWindow
sans changer le comportement.
"""

from typing import Any

from . import panels


class OverlayManager:
    def __init__(self, win: Any) -> None:
        self.win = win

    # Construction / Positionnement
    def build_overlays(self) -> None:
        self.win.library_overlay, self.win.library_widget, self.win.inspector_overlay, self.win.inspector_widget = panels.build_side_overlays(self.win)

    def position_overlays(self) -> None:
        panels.position_overlays(self.win)

    # Visibilité
    def set_library_visible(self, visible: bool) -> None:
        self.win.library_overlay.setVisible(visible)
        self.win.toggle_library_action.blockSignals(True)
        self.win.toggle_library_action.setChecked(visible)
        self.win.toggle_library_action.blockSignals(False)

    def set_inspector_visible(self, visible: bool) -> None:
        self.win.inspector_overlay.setVisible(visible)
        self.win.toggle_inspector_action.blockSignals(True)
        self.win.toggle_inspector_action.setChecked(visible)
        self.win.toggle_inspector_action.blockSignals(False)

    def set_custom_visible(self, visible: bool) -> None:
        overlay = getattr(self.win.view, '_custom_tools_overlay', None)
        if overlay is not None:
            overlay.setVisible(visible)
        self.win.toggle_custom_action.blockSignals(True)
        self.win.toggle_custom_action.setChecked(visible)
        self.win.toggle_custom_action.blockSignals(False)

    # Menus / icônes
    def apply_menu_settings(self) -> None:
        try:
            self.win.view.apply_menu_settings_main()
            self.win.view.apply_menu_settings_quick()
        except Exception:
            pass

    def refresh_overlay_icons(self) -> None:
        try:
            self.win.view.refresh_overlay_icons(self.win)
        except Exception:
            pass

