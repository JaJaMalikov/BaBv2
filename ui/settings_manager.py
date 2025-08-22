"""Module for managing application settings, including UI layout and theme."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

import ui.icons as app_icons
from ui.styles import apply_stylesheet
from ui.ui_profile import UIProfile

from . import settings_geometry, settings_shortcuts, settings_theme

# QSettings keys used here (maintenance):
# UI_THEME, UI_THEME_FILE, UI_CUSTOM_PARAM handle theme configuration.
# ONION_PREV_COUNT, ONION_NEXT_COUNT, ONION_OPACITY_PREV, ONION_OPACITY_NEXT
# manage onion skin defaults.
from ui.settings_keys import (
    UI_THEME,
    UI_THEME_FILE,
    UI_CUSTOM_PARAM,
    ONION_PREV_COUNT,
    ONION_NEXT_COUNT,
    ONION_OPACITY_PREV,
    ONION_OPACITY_NEXT,
)


class SettingsManager:
    """Encapsulates the saving and restoring of UI settings (geometries, visibility)."""

    def __init__(self, win: Any, org: str = "JaJa", app: str = "Macronotron") -> None:
        """
        Initializes the SettingsManager.

        Args:
            win: The main window instance.
            org: QSettings organization scope (default: "JaJa").
            app: QSettings application scope (default: "Macronotron").
        """
        self.win = win
        self.org = org
        self.app = app


    def save(self) -> None:
        """Saves the current UI settings."""
        settings_geometry.save(self.win, self.org, self.app)

    def load(self) -> None:
        """Loads the UI settings."""
        settings_geometry.load(self.win, self.org, self.app)
        settings_shortcuts.load(self.win, self.org, self.app)


    def clear(self) -> None:
        """Clear persisted UI layout state only (geometry/layout keys)."""
        settings_geometry.clear(self.org, self.app)

    def _apply_all_settings(self, dlg: Any, s: QSettings) -> None:
        """Apply settings from the dialog widgets into QSettings and refresh UI."""
        settings_theme.apply_all_settings(self.win, dlg, s)

    def _export_profile_from_dialog(self, dlg: Any) -> None:
        """Export a UIProfile built from current dialog fields."""
        try:
            from PySide6.QtWidgets import QFileDialog

            prof = UIProfile.from_dialog(dlg)
            path, _ = QFileDialog.getSaveFileName(
                dlg, "Exporter le profil UI", "ui_profile.json", "JSON (*.json)"
            )
            if path:
                prof.export_json(path)
        except Exception:
            logging.exception("Export UI profile failed")

    def _import_profile_into_dialog(self, dlg: Any) -> None:
        """Import a UIProfile from a chosen JSON file and populate dialog fields."""
        try:
            from PySide6.QtWidgets import QFileDialog

            path, _ = QFileDialog.getOpenFileName(
                dlg, "Importer un profil UI", "", "JSON (*.json)"
            )
            if not path:
                return
            prof = UIProfile.import_json(path)
            prof.to_dialog(dlg)
        except Exception:
            logging.exception("Import UI profile failed")

    def _reset_profile_default_in_dialog(self, dlg: Any) -> None:
        """Reset dialog fields to default dark UIProfile values without persisting."""
        try:
            UIProfile.default_dark().to_dialog(dlg)
        except Exception:
            logging.exception("Reset UI profile failed")

    def export_profile(self, path: str) -> bool:
        """Export current UI profile to the given JSON file path (no dialogs).

        Returns True on success, False on failure.
        """
        try:
            prof = UIProfile.from_qsettings(QSettings(self.org, self.app))
            prof.export_json(path)
            return True
        except Exception:
            logging.exception("Export UI profile to %s failed", path)
            return False

    def import_profile(self, path: str) -> bool:
        """Import a UI profile JSON from the given path and apply to QSettings.

        This method refreshes icons, menus, and stylesheet to reflect changes.
        Returns True on success, False on failure.
        """
        try:
            prof = UIProfile.import_json(path)
            prof.apply_to_qsettings(QSettings(self.org, self.app))
            # Refresh icons and menus
            try:
                app_icons.clear_cache()
                if hasattr(self.win, "save_action"):
                    self.win.save_action.setIcon(app_icons.icon_save())
                if hasattr(self.win, "load_action"):
                    self.win.load_action.setIcon(app_icons.icon_open())
                if hasattr(self.win, "scene_size_action"):
                    self.win.scene_size_action.setIcon(app_icons.icon_scene_size())
                if hasattr(self.win, "background_action"):
                    self.win.background_action.setIcon(app_icons.icon_background())
                if hasattr(self.win, "reset_scene_action"):
                    self.win.reset_scene_action.setIcon(app_icons.icon_reset_scene())
                if hasattr(self.win, "reset_ui_action"):
                    self.win.reset_ui_action.setIcon(app_icons.icon_reset_ui())
                if hasattr(self.win, "toggle_library_action"):
                    self.win.toggle_library_action.setIcon(app_icons.icon_library())
                if hasattr(self.win, "toggle_inspector_action"):
                    self.win.toggle_inspector_action.setIcon(app_icons.icon_inspector())
                if hasattr(self.win, "timeline_dock"):
                    self.win.timeline_dock.toggleViewAction().setIcon(
                        app_icons.icon_timeline()
                    )
                if hasattr(self.win, "view"):
                    try:
                        self.win.view.refresh_overlay_icons(self.win)
                        self.win.view.apply_menu_settings_main()
                        self.win.view.apply_menu_settings_quick()
                    except Exception:
                        logging.exception(
                            "Failed to refresh overlay icons or menu settings after import"
                        )
                if hasattr(self.win, "timeline_widget"):
                    self.win.timeline_widget.update()
            except Exception:
                logging.exception("Failed to refresh UI after importing profile")
            # Apply stylesheet
            apply_stylesheet(QApplication.instance())
            return True
        except Exception:
            logging.exception("Import UI profile from %s failed", path)
            return False

    def open_dialog(self) -> None:
        """Opens the settings dialog and applies the changes if accepted."""
        from ui.settings_dialog import SettingsDialog

        win = self.win
        dlg = SettingsDialog(win)
        if hasattr(win, "shortcuts"):
            dlg.set_shortcut_actions(win.shortcuts)

        s = QSettings(self.org, self.app)

        theme = str(s.value(UI_THEME, "dark")).lower()
        if theme == "custom":
            from pathlib import Path

            theme_path = s.value(UI_THEME_FILE) or str(
                Path.home() / ".config/JaJa/Macronotron/theme.json"
            )
            try:
                p = Path(str(theme_path))
                if p.exists():
                    import json

                    data = json.load(p.open("r", encoding="utf-8"))
                    if isinstance(data, dict):
                        for k, v in data.items():
                            s.setValue(UI_CUSTOM_PARAM(k), v)
            except Exception:
                logging.exception("Failed to read theme file")

        prof = UIProfile.from_qsettings(s)
        prof.to_dialog(dlg)

        # Default sizes from current overlays
        try:
            dlg.lib_w.setValue(win.library_overlay.width())
            dlg.lib_h.setValue(win.library_overlay.height())
            dlg.insp_w.setValue(win.inspector_overlay.width())
            dlg.insp_h.setValue(win.inspector_overlay.height())
            # Positions
            dlg.lib_x.setValue(win.library_overlay.x())
            dlg.lib_y.setValue(win.library_overlay.y())
            dlg.insp_x.setValue(win.inspector_overlay.x())
            dlg.insp_y.setValue(win.inspector_overlay.y())
            cust = getattr(win.view, "_custom_tools_overlay", None)
            if cust is not None:
                dlg.cust_x.setValue(cust.x())
                dlg.cust_y.setValue(cust.y())
                dlg.cust_w.setValue(cust.width())
                dlg.cust_h.setValue(cust.height())
        except (RuntimeError, AttributeError):
            logging.exception("Failed to load default overlay sizes")

        # Onion values
        try:
            dlg.prev_count.setValue(int(s.value(ONION_PREV_COUNT, 2)))
            dlg.next_count.setValue(int(s.value(ONION_NEXT_COUNT, 1)))
            dlg.opacity_prev.setValue(float(s.value(ONION_OPACITY_PREV, 0.25)))
            dlg.opacity_next.setValue(float(s.value(ONION_OPACITY_NEXT, 0.18)))
        except (ValueError, TypeError):
            logging.exception("Failed to load onion settings")

        try:
            dlg.btn_export_profile.clicked.connect(
                lambda: self._export_profile_from_dialog(dlg)
            )
            dlg.btn_import_profile.clicked.connect(
                lambda: self._import_profile_into_dialog(dlg)
            )
            dlg.btn_reset_profile.clicked.connect(
                lambda: self._reset_profile_default_in_dialog(dlg)
            )
        except Exception:
            logging.exception("Failed to connect UI profile buttons")

        if dlg.exec() == SettingsDialog.Accepted:
            try:
                prof = UIProfile.from_dialog(dlg)

                # Persistance centralisée
                prof.apply_to_qsettings(s)

                # Raccourcis
                if hasattr(win, "shortcuts"):
                    s.beginGroup("shortcuts")
                    for key, seq in dlg.get_shortcuts().items():
                        s.setValue(key, seq)
                        win.shortcuts[key].setShortcut(seq)
                    s.endGroup()

                # Rafraîchir UI
                try:
                    app_icons.clear_cache()
                    self.win.view.refresh_overlay_icons(self.win)
                    self.win.view.apply_menu_settings_main()
                    self.win.view.apply_menu_settings_quick()
                    self.win.timeline_widget.update()
                except Exception:
                    pass
                apply_stylesheet(QApplication.instance())
            except Exception:
                logging.exception("Failed to persist UIProfile from dialog")
