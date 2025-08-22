"""Module for managing application settings, including UI layout and theme."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

import ui.icons as app_icons
from ui.styles import apply_stylesheet
from ui.ui_profile import UIProfile, _int, _float

from . import settings_geometry, settings_shortcuts, settings_theme


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
        settings_theme.export_profile_from_dialog(dlg)

    def _import_profile_into_dialog(self, dlg: Any) -> None:
        """Import a UIProfile from a chosen JSON file and populate dialog fields."""
        settings_theme.import_profile_into_dialog(dlg)

    def _reset_profile_default_in_dialog(self, dlg: Any) -> None:
        """Reset dialog fields to default dark UIProfile values without persisting."""
        settings_theme.reset_profile_default_in_dialog(dlg)

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
        from ui.settings_keys import UI_ICON_DIR, UI_ICON_SIZE, UI_THEME, UI_THEME_FILE, UI_STYLE_SCENE_BG, UI_FONT_FAMILY, UI_MENU_CUSTOM_VISIBLE, UI_CUSTOM_PARAMS_GROUP, UI_CUSTOM_PARAM, UI_ICON_COLOR_NORMAL, UI_ICON_COLOR_HOVER, UI_ICON_COLOR_ACTIVE, TIMELINE_BG, TIMELINE_RULER_BG, TIMELINE_TRACK_BG, TIMELINE_TICK, TIMELINE_TICK_MAJOR, TIMELINE_PLAYHEAD, TIMELINE_KF, TIMELINE_KF_HOVER
        icon_dir = s.value(UI_ICON_DIR)
        if icon_dir:
            try:
                dlg.icon_dir_edit.setText(str(icon_dir))
            except (RuntimeError, AttributeError):
                logging.exception("Failed to set icon directory text")
        try:
            dlg.icon_size_spin.setValue(_int(s.value(UI_ICON_SIZE), 32))
        except (TypeError, ValueError):
            dlg.icon_size_spin.setValue(32)
        theme = str(s.value(UI_THEME, "dark")).lower()
        try:
            presets_map = {
                "light": "Light",
                "dark": "Dark",
                "high contrast": "High Contrast",
                "custom": "Custom",
            }
            dlg.preset_combo.setCurrentText(presets_map.get(theme, "Dark"))
            if theme == "custom":
                # Load from theme file if present, else from custom_params
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
                                s.setValue(f"ui/custom_params/{k}", v)
                except Exception:
                    logging.exception("Failed to read theme file")
                s.beginGroup(UI_CUSTOM_PARAMS_GROUP)

                def _gv(key: str, default: str) -> str:
                    v = s.value(key)
                    return str(v) if v not in [None, ""] else default

                try:
                    dlg.bg_edit.setText(_gv("bg_color", "#E2E8F0"))
                    dlg.text_edit.setText(_gv("text_color", "#1A202C"))
                    dlg.accent_edit.setText(_gv("accent_color", "#E53E3E"))
                    dlg.hover_edit.setText(_gv("hover_color", "#E3E6FD"))
                    dlg.panel_edit.setText(_gv("panel_bg", "#F7F8FC"))
                    dlg.border_edit.setText(_gv("panel_border", "#D0D5DD"))
                    # Header styles (persisted under ui/custom_params)
                    dlg.header_bg_edit.setText(_gv("header_bg", ""))
                    dlg.header_text_edit.setText(
                        _gv("header_text", dlg.text_edit.text())
                    )
                    dlg.header_border_edit.setText(
                        _gv("header_border", dlg.border_edit.text())
                    )
                    dlg.group_edit.setText(_gv("group_title_color", "#2D3748"))
                    dlg.tooltip_bg_edit.setText(
                        _gv("tooltip_bg", dlg.panel_edit.text())
                    )
                    dlg.tooltip_text_edit.setText(
                        _gv("tooltip_text", dlg.text_edit.text())
                    )
                    # Nouveaux champs exposés
                    dlg.input_bg_edit.setText(_gv("input_bg", "#EDF2F7"))
                    dlg.input_border_edit.setText(_gv("input_border", "#CBD5E0"))
                    dlg.input_text_edit.setText(_gv("input_text", dlg.text_edit.text()))
                    dlg.input_focus_bg_edit.setText(_gv("input_focus_bg", "#FFFFFF"))
                    dlg.input_focus_border_edit.setText(
                        _gv("input_focus_border", dlg.accent_edit.text())
                    )
                    dlg.list_hover_edit.setText(_gv("list_hover_bg", "#E2E8F0"))
                    dlg.list_sel_bg_edit.setText(
                        _gv("list_selected_bg", dlg.accent_edit.text())
                    )
                    dlg.list_sel_text_edit.setText(_gv("list_selected_text", "#FFFFFF"))
                    dlg.cb_un_bg_edit.setText(_gv("checkbox_unchecked_bg", "#EDF2F7"))
                    dlg.cb_un_border_edit.setText(
                        _gv("checkbox_unchecked_border", "#A0AEC0")
                    )
                    dlg.cb_ch_bg_edit.setText(
                        _gv("checkbox_checked_bg", dlg.accent_edit.text())
                    )
                    dlg.cb_ch_border_edit.setText(
                        _gv("checkbox_checked_border", "#C53030")
                    )
                    dlg.cb_ch_hover_edit.setText(
                        _gv("checkbox_checked_hover", "#F56565")
                    )
                    # Numeric params
                    try:
                        dlg.opacity_spin.setValue(
                            int(_float(s.value("panel_opacity"), 0.9) * 100)
                        )
                    except Exception:
                        dlg.opacity_spin.setValue(90)
                    dlg.radius_spin.setValue(_int(s.value("radius"), 12))
                    dlg.font_spin.setValue(_int(s.value("font_size"), 10))
                    dlg.font_family_edit.setText(
                        _gv("font_family", str(s.value(UI_FONT_FAMILY) or "Poppins"))
                    )
                except Exception:
                    logging.exception("Failed to load custom params")
                finally:
                    s.endGroup()
                try:
                    dlg._update_all_swatches()
                    dlg._preview_theme()
                except Exception:
                    pass
            else:
                dlg._load_preset_values(dlg.preset_combo.currentText())
        except (RuntimeError, AttributeError):
            logging.exception("Failed to load preset/custom values")
        # Font family default if not set via custom
        try:
            if not dlg.font_family_edit.text().strip():
                from ui.settings_keys import UI_FONT_FAMILY
                fam = s.value(UI_FONT_FAMILY) or "Poppins"
                dlg.font_family_edit.setText(str(fam))
        except (RuntimeError, AttributeError):
            logging.exception("Failed to set font family edit")
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

        # Menu builder defaults via helpers
        from ui.settings_keys import UI_MENU_CUSTOM_VISIBLE
        dlg.cb_custom_visible.setChecked(
            settings_theme.get_bool_setting(s, UI_MENU_CUSTOM_VISIBLE, False)
        )

        # Populate icon lists with order + visibility

        from ui.menu_defaults import (
            MAIN_DEFAULT_ORDER,
            QUICK_DEFAULT_ORDER,
            CUSTOM_DEFAULT_ORDER,
        )

        main_default = list(MAIN_DEFAULT_ORDER)
        quick_default = list(QUICK_DEFAULT_ORDER)
        custom_default = list(CUSTOM_DEFAULT_ORDER)
        main_order, main_vis = settings_theme.get_order_and_vis(
            s, "main", main_default
        )
        quick_order, quick_vis = settings_theme.get_order_and_vis(
            s, "quick", quick_default
        )
        custom_order, custom_vis = settings_theme.get_order_and_vis(
            s, "custom", custom_default
        )
        try:
            dlg.populate_icon_list(
                dlg.list_main_order, main_order, main_vis, dlg._main_specs
            )
            dlg.populate_icon_list(
                dlg.list_quick_order, quick_order, quick_vis, dlg._quick_specs
            )
            dlg.populate_icon_list(
                dlg.list_custom_order, custom_order, custom_vis, dlg._custom_specs
            )
        except (RuntimeError, AttributeError):
            logging.exception("Failed to populate icon lists")

        # Load icon color fields if present
        try:
            if hasattr(dlg, "icon_norm_edit"):
                s_ic = QSettings(self.org, self.app)
                from ui.settings_keys import (
                    UI_ICON_COLOR_NORMAL,
                    UI_ICON_COLOR_HOVER,
                    UI_ICON_COLOR_ACTIVE,
                )
                dlg.icon_norm_edit.setText(str(s_ic.value(UI_ICON_COLOR_NORMAL) or "#4A5568"))
                dlg.icon_hover_edit.setText(str(s_ic.value(UI_ICON_COLOR_HOVER) or "#E53E3E"))
                dlg.icon_active_edit.setText(str(s_ic.value(UI_ICON_COLOR_ACTIVE) or "#FFFFFF"))
        except Exception:
            logging.exception("Failed to preload icon colors")

        # Preload timeline colors
        try:
            from ui.settings_keys import (
                TIMELINE_BG,
                TIMELINE_RULER_BG,
                TIMELINE_TRACK_BG,
                TIMELINE_TICK,
                TIMELINE_TICK_MAJOR,
                TIMELINE_PLAYHEAD,
                TIMELINE_KF,
                TIMELINE_KF_HOVER,
                TIMELINE_INOUT_ALPHA,
            )
            dlg.tl_bg.setText(str(s.value(TIMELINE_BG) or "#1E1E1E"))
            dlg.tl_ruler_bg.setText(str(s.value(TIMELINE_RULER_BG) or "#2C2C2C"))
            dlg.tl_track_bg.setText(str(s.value(TIMELINE_TRACK_BG) or "#242424"))
            dlg.tl_tick.setText(str(s.value(TIMELINE_TICK) or "#8A8A8A"))
            dlg.tl_tick_major.setText(str(s.value(TIMELINE_TICK_MAJOR) or "#E0E0E0"))
            dlg.tl_playhead.setText(str(s.value(TIMELINE_PLAYHEAD) or "#65B0FF"))
            dlg.tl_kf.setText(str(s.value(TIMELINE_KF) or "#FFC107"))
            dlg.tl_kf_hover.setText(str(s.value(TIMELINE_KF_HOVER) or "#FFE082"))
            try:
                dlg.tl_inout_alpha.setValue(int(s.value(TIMELINE_INOUT_ALPHA, 30)))
            except Exception:
                dlg.tl_inout_alpha.setValue(30)
        except Exception:
            logging.exception("Failed to preload timeline colors")

        # Preload scene background color
        try:
            from ui.settings_keys import UI_STYLE_SCENE_BG
            dlg.scene_bg_edit.setText(str(s.value(UI_STYLE_SCENE_BG) or ""))
        except Exception:
            logging.exception("Failed to preload scene background color")

        # Onion values
        try:
            from ui.settings_keys import (
                ONION_PREV_COUNT,
                ONION_NEXT_COUNT,
                ONION_OPACITY_PREV,
                ONION_OPACITY_NEXT,
            )
            dlg.prev_count.setValue(int(s.value(ONION_PREV_COUNT, 2)))
            dlg.next_count.setValue(int(s.value(ONION_NEXT_COUNT, 1)))
            dlg.opacity_prev.setValue(float(s.value(ONION_OPACITY_PREV, 0.25)))
            dlg.opacity_next.setValue(float(s.value(ONION_OPACITY_NEXT, 0.18)))
        except (ValueError, TypeError):
            logging.exception("Failed to load onion settings")

        # Import/Export/Reset profile (ne sauvegardent pas tant que le dialog n'est pas validé)
        def _export_profile() -> None:
            try:
                from PySide6.QtWidgets import QFileDialog

                prof = UIProfile()
                # Récupère les champs du dialog
                prof.theme.preset = dlg.preset_combo.currentText().strip().lower()
                prof.theme.font_family = (
                    dlg.font_family_edit.text().strip() or "Poppins"
                )
                if prof.theme.preset == "custom":
                    prof.theme.custom_params.update(
                        {
                            "bg_color": dlg.bg_edit.text() or "#E2E8F0",
                            "text_color": dlg.text_edit.text() or "#1A202C",
                            "accent_color": dlg.accent_edit.text() or "#E53E3E",
                            "hover_color": dlg.hover_edit.text() or "#E3E6FD",
                            "panel_bg": dlg.panel_edit.text() or "#F7F8FC",
                            "panel_opacity": (dlg.opacity_spin.value() / 100.0),
                            "panel_border": dlg.border_edit.text() or "#D0D5DD",
                            "header_bg": dlg.header_bg_edit.text() or "",
                            "header_text": dlg.header_text_edit.text()
                            or dlg.text_edit.text()
                            or "#1A202C",
                            "header_border": dlg.header_border_edit.text()
                            or dlg.border_edit.text()
                            or "#D0D5DD",
                            "group_title_color": dlg.group_edit.text() or "#2D3748",
                            "tooltip_bg": dlg.tooltip_bg_edit.text() or "#F7F8FC",
                            "tooltip_text": dlg.tooltip_text_edit.text() or "#1A202C",
                            "tooltip_border": dlg.border_edit.text() or "#D0D5DD",
                            "radius": dlg.radius_spin.value(),
                            "font_size": dlg.font_spin.value(),
                            "font_family": dlg.font_family_edit.text() or "Poppins",
                        }
                    )
                prof.icon_dir = dlg.icon_dir_edit.text().strip() or None
                prof.icon_size = int(dlg.icon_size_spin.value())
                if hasattr(dlg, "icon_norm_edit"):
                    prof.icon_color_normal = (
                        dlg.icon_norm_edit.text().strip() or prof.icon_color_normal
                    )
                    prof.icon_color_hover = (
                        dlg.icon_hover_edit.text().strip() or prof.icon_color_hover
                    )
                    prof.icon_color_active = (
                        dlg.icon_active_edit.text().strip() or prof.icon_color_active
                    )
                prof.timeline_bg = dlg.tl_bg.text().strip() or prof.timeline_bg
                prof.timeline_ruler_bg = (
                    dlg.tl_ruler_bg.text().strip() or prof.timeline_ruler_bg
                )
                prof.timeline_track_bg = (
                    dlg.tl_track_bg.text().strip() or prof.timeline_track_bg
                )
                prof.timeline_tick = dlg.tl_tick.text().strip() or prof.timeline_tick
                prof.timeline_tick_major = (
                    dlg.tl_tick_major.text().strip() or prof.timeline_tick_major
                )
                prof.timeline_playhead = (
                    dlg.tl_playhead.text().strip() or prof.timeline_playhead
                )
                prof.timeline_kf = dlg.tl_kf.text().strip() or prof.timeline_kf
                prof.timeline_kf_hover = (
                    dlg.tl_kf_hover.text().strip() or prof.timeline_kf_hover
                )
                prof.timeline_inout_alpha = int(dlg.tl_inout_alpha.value())
                prof.scene_bg = dlg.scene_bg_edit.text().strip() or None
                m_order, m_vis = dlg.extract_icon_list(dlg.list_main_order)
                q_order, q_vis = dlg.extract_icon_list(dlg.list_quick_order)
                c_order, c_vis = dlg.extract_icon_list(dlg.list_custom_order)
                prof.menu_main_order, prof.menu_main_vis = m_order, m_vis
                prof.menu_quick_order, prof.menu_quick_vis = q_order, q_vis
                prof.menu_custom_order, prof.menu_custom_vis = c_order, c_vis
                path, _ = QFileDialog.getSaveFileName(
                    dlg, "Exporter le profil UI", "ui_profile.json", "JSON (*.json)"
                )
                if path:
                    prof.export_json(path)
            except Exception:
                logging.exception("Export UI profile failed")

        def _import_profile() -> None:
            try:
                from PySide6.QtWidgets import QFileDialog

                path, _ = QFileDialog.getOpenFileName(
                    dlg, "Importer un profil UI", "", "JSON (*.json)"
                )
                if not path:
                    return
                prof = UIProfile.import_json(path)
                # Renseigne les champs du dialog seulement
                presets_map = {
                    "light": "Light",
                    "dark": "Dark",
                    "high contrast": "High Contrast",
                    "custom": "Custom",
                }
                dlg.preset_combo.setCurrentText(
                    presets_map.get(prof.theme.preset, "Dark")
                )
                dlg.font_family_edit.setText(prof.theme.font_family or "Poppins")
                if prof.theme.preset == "custom":
                    cp = prof.theme.custom_params
                    dlg.bg_edit.setText(str(cp.get("bg_color", "#E2E8F0")))
                    dlg.text_edit.setText(str(cp.get("text_color", "#1A202C")))
                    dlg.accent_edit.setText(str(cp.get("accent_color", "#E53E3E")))
                    dlg.hover_edit.setText(str(cp.get("hover_color", "#E3E6FD")))
                    dlg.panel_edit.setText(str(cp.get("panel_bg", "#F7F8FC")))
                    dlg.border_edit.setText(str(cp.get("panel_border", "#D0D5DD")))
                    dlg.header_bg_edit.setText(str(cp.get("header_bg", "")))
                    dlg.header_text_edit.setText(
                        str(cp.get("header_text", dlg.text_edit.text()))
                    )
                    dlg.header_border_edit.setText(
                        str(cp.get("header_border", dlg.border_edit.text()))
                    )
                    dlg.group_edit.setText(str(cp.get("group_title_color", "#2D3748")))
                    dlg.tooltip_bg_edit.setText(
                        str(cp.get("tooltip_bg", dlg.panel_edit.text()))
                    )
                    dlg.tooltip_text_edit.setText(
                        str(cp.get("tooltip_text", dlg.text_edit.text()))
                    )
                    try:
                        dlg.opacity_spin.setValue(
                            int(float(cp.get("panel_opacity", 0.9)) * 100)
                        )
                    except Exception:
                        dlg.opacity_spin.setValue(90)
                    dlg.radius_spin.setValue(int(cp.get("radius", 12)))
                    dlg.font_spin.setValue(int(cp.get("font_size", 10)))
                dlg.icon_dir_edit.setText(str(prof.icon_dir or ""))
                dlg.icon_size_spin.setValue(int(prof.icon_size))
                if hasattr(dlg, "icon_norm_edit"):
                    dlg.icon_norm_edit.setText(str(prof.icon_color_normal))
                    dlg.icon_hover_edit.setText(str(prof.icon_color_hover))
                    dlg.icon_active_edit.setText(str(prof.icon_color_active))
                dlg.tl_bg.setText(prof.timeline_bg)
                dlg.tl_ruler_bg.setText(prof.timeline_ruler_bg)
                dlg.tl_track_bg.setText(prof.timeline_track_bg)
                dlg.tl_tick.setText(prof.timeline_tick)
                dlg.tl_tick_major.setText(prof.timeline_tick_major)
                dlg.tl_playhead.setText(prof.timeline_playhead)
                dlg.tl_kf.setText(prof.timeline_kf)
                dlg.tl_kf_hover.setText(prof.timeline_kf_hover)
                dlg.tl_inout_alpha.setValue(int(prof.timeline_inout_alpha))
                dlg.scene_bg_edit.setText(str(prof.scene_bg or ""))
                dlg.cb_custom_visible.setChecked(bool(prof.custom_overlay_visible))
                try:
                    dlg.populate_icon_list(
                        dlg.list_main_order,
                        prof.menu_main_order,
                        prof.menu_main_vis,
                        dlg._main_specs,
                    )
                    dlg.populate_icon_list(
                        dlg.list_quick_order,
                        prof.menu_quick_order,
                        prof.menu_quick_vis,
                        dlg._quick_specs,
                    )
                    dlg.populate_icon_list(
                        dlg.list_custom_order,
                        prof.menu_custom_order,
                        prof.menu_custom_vis,
                        dlg._custom_specs,
                    )
                except Exception:
                    pass
            except Exception:
                logging.exception("Import UI profile failed")

        def _reset_profile_default() -> None:
            try:
                prof = UIProfile.default_dark()
                # Mettez les champs aux valeurs défaut Dark
                dlg.preset_combo.setCurrentText("Dark")
                dlg.font_family_edit.setText(prof.theme.font_family)
                # Timeline / icônes vers valeurs par défaut
                dlg.icon_dir_edit.setText("")
                dlg.icon_size_spin.setValue(int(prof.icon_size))
                if hasattr(dlg, "icon_norm_edit"):
                    dlg.icon_norm_edit.setText(prof.icon_color_normal)
                    dlg.icon_hover_edit.setText(prof.icon_color_hover)
                    dlg.icon_active_edit.setText(prof.icon_color_active)
                dlg.tl_bg.setText(prof.timeline_bg)
                dlg.tl_ruler_bg.setText(prof.timeline_ruler_bg)
                dlg.tl_track_bg.setText(prof.timeline_track_bg)
                dlg.tl_tick.setText(prof.timeline_tick)
                dlg.tl_tick_major.setText(prof.timeline_tick_major)
                dlg.tl_playhead.setText(prof.timeline_playhead)
                dlg.tl_kf.setText(prof.timeline_kf)
                dlg.tl_kf_hover.setText(prof.timeline_kf_hover)
                dlg.tl_inout_alpha.setValue(int(prof.timeline_inout_alpha))
                dlg.scene_bg_edit.setText("")
                dlg.cb_custom_visible.setChecked(False)
            except Exception:
                logging.exception("Reset UI profile failed")

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
            # Construire un profil complet à partir des champs et l'appliquer
            try:
                prof = UIProfile()
                prof.theme.preset = (
                    dlg.preset_combo.currentText().strip().lower() or "dark"
                )
                prof.theme.font_family = (
                    dlg.font_family_edit.text().strip() or "Poppins"
                )
                if prof.theme.preset == "custom":
                    prof.theme.custom_params.update(
                        {
                            "bg_color": dlg.bg_edit.text() or "#E2E8F0",
                            "text_color": dlg.text_edit.text() or "#1A202C",
                            "accent_color": dlg.accent_edit.text() or "#E53E3E",
                            "hover_color": dlg.hover_edit.text() or "#E3E6FD",
                            "panel_bg": dlg.panel_edit.text() or "#F7F8FC",
                            "panel_opacity": (dlg.opacity_spin.value() / 100.0),
                            "panel_border": dlg.border_edit.text() or "#D0D5DD",
                            "header_bg": dlg.header_bg_edit.text() or "",
                            "header_text": dlg.header_text_edit.text()
                            or dlg.text_edit.text()
                            or "#1A202C",
                            "header_border": dlg.header_border_edit.text()
                            or dlg.border_edit.text()
                            or "#D0D5DD",
                            "group_title_color": dlg.group_edit.text() or "#2D3748",
                            "tooltip_bg": dlg.tooltip_bg_edit.text() or "#F7F8FC",
                            "tooltip_text": dlg.tooltip_text_edit.text() or "#1A202C",
                            "tooltip_border": dlg.border_edit.text() or "#D0D5DD",
                            "radius": dlg.radius_spin.value(),
                            "font_size": dlg.font_spin.value(),
                            "font_family": dlg.font_family_edit.text() or "Poppins",
                            # Champs supplémentaires exposés
                            "input_bg": dlg.input_bg_edit.text() or "#EDF2F7",
                            "input_border": dlg.input_border_edit.text() or "#CBD5E0",
                            "input_text": dlg.input_text_edit.text()
                            or (dlg.text_edit.text() or "#1A202C"),
                            "input_focus_bg": dlg.input_focus_bg_edit.text()
                            or "#FFFFFF",
                            "input_focus_border": dlg.input_focus_border_edit.text()
                            or (dlg.accent_edit.text() or "#E53E3E"),
                            "list_hover_bg": dlg.list_hover_edit.text() or "#E2E8F0",
                            "list_selected_bg": dlg.list_sel_bg_edit.text()
                            or (dlg.accent_edit.text() or "#E53E3E"),
                            "list_selected_text": dlg.list_sel_text_edit.text()
                            or "#FFFFFF",
                            "checkbox_unchecked_bg": dlg.cb_un_bg_edit.text()
                            or "#EDF2F7",
                            "checkbox_unchecked_border": dlg.cb_un_border_edit.text()
                            or "#A0AEC0",
                            "checkbox_checked_bg": dlg.cb_ch_bg_edit.text()
                            or (dlg.accent_edit.text() or "#E53E3E"),
                            "checkbox_checked_border": dlg.cb_ch_border_edit.text()
                            or "#C53030",
                            "checkbox_checked_hover": dlg.cb_ch_hover_edit.text()
                            or "#F56565",
                        }
                    )
                # Icônes/timeline/menus/scène
                prof.icon_dir = dlg.icon_dir_edit.text().strip() or None
                prof.icon_size = int(dlg.icon_size_spin.value())
                if hasattr(dlg, "icon_norm_edit"):
                    prof.icon_color_normal = (
                        dlg.icon_norm_edit.text().strip() or prof.icon_color_normal
                    )
                    prof.icon_color_hover = (
                        dlg.icon_hover_edit.text().strip() or prof.icon_color_hover
                    )
                    prof.icon_color_active = (
                        dlg.icon_active_edit.text().strip() or prof.icon_color_active
                    )
                prof.timeline_bg = dlg.tl_bg.text().strip() or prof.timeline_bg
                prof.timeline_ruler_bg = (
                    dlg.tl_ruler_bg.text().strip() or prof.timeline_ruler_bg
                )
                prof.timeline_track_bg = (
                    dlg.tl_track_bg.text().strip() or prof.timeline_track_bg
                )
                prof.timeline_tick = dlg.tl_tick.text().strip() or prof.timeline_tick
                prof.timeline_tick_major = (
                    dlg.tl_tick_major.text().strip() or prof.timeline_tick_major
                )
                prof.timeline_playhead = (
                    dlg.tl_playhead.text().strip() or prof.timeline_playhead
                )
                prof.timeline_kf = dlg.tl_kf.text().strip() or prof.timeline_kf
                prof.timeline_kf_hover = (
                    dlg.tl_kf_hover.text().strip() or prof.timeline_kf_hover
                )
                prof.timeline_inout_alpha = int(dlg.tl_inout_alpha.value())
                prof.scene_bg = dlg.scene_bg_edit.text().strip() or None
                m_order, m_vis = dlg.extract_icon_list(dlg.list_main_order)
                q_order, q_vis = dlg.extract_icon_list(dlg.list_quick_order)
                c_order, c_vis = dlg.extract_icon_list(dlg.list_custom_order)
                prof.menu_main_order, prof.menu_main_vis = m_order, m_vis
                prof.menu_quick_order, prof.menu_quick_vis = q_order, q_vis
                prof.menu_custom_order, prof.menu_custom_vis = c_order, c_vis
                prof.custom_overlay_visible = dlg.cb_custom_visible.isChecked()

                # Géométries (optionnelles)
                prof.geom_library = (
                    dlg.lib_x.value(),
                    dlg.lib_y.value(),
                    dlg.lib_w.value(),
                    dlg.lib_h.value(),
                )
                prof.geom_inspector = (
                    dlg.insp_x.value(),
                    dlg.insp_y.value(),
                    dlg.insp_w.value(),
                    dlg.insp_h.value(),
                )

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
