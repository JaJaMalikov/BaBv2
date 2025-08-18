"""Module for managing application settings, including UI layout and theme."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

import ui.icons as app_icons
from ui.styles import apply_stylesheet, build_stylesheet
from ui.ui_profile import UIProfile


def load_active_profile() -> UIProfile:
    """Charge le profil UI courant depuis le stockage persistant."""
    try:
        return UIProfile.from_qsettings(QSettings("JaJa", "Macronotron"))
    except Exception:
        logging.exception("Failed to load UIProfile; using default dark")
        return UIProfile.default_dark()


class SettingsManager:
    """Encapsulates the saving and restoring of UI settings (geometries, visibility)."""

    def __init__(self, win: Any) -> None:
        """
        Initializes the SettingsManager.

        Args:
            win: The main window instance.
        """
        self.win = win
        self.org = "JaJa"
        self.app = "Macronotron"

    def save(self) -> None:
        """Saves the current UI settings."""
        s = QSettings(self.org, self.app)
        s.setValue("geometry/mainwindow", self.win.saveGeometry())
        s.setValue("geometry/library", self.win.library_overlay.geometry())
        s.setValue("geometry/inspector", self.win.inspector_overlay.geometry())
        s.setValue("layout/timeline_visible", self.win.timeline_dock.isVisible())
        if hasattr(self.win.view, "_overlay") and self.win.view._overlay:
            s.setValue("geometry/view_toolbar", self.win.view._overlay.geometry())
        if (
            hasattr(self.win.view, "_main_tools_overlay")
            and self.win.view._main_tools_overlay
        ):
            s.setValue(
                "geometry/main_toolbar", self.win.view._main_tools_overlay.geometry()
            )

    def load(self) -> None:
        """Loads the UI settings."""
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
            self.win.timeline_dock.setVisible(is_visible in [True, "true"])
        if (
            hasattr(self.win.view, "_overlay")
            and self.win.view._overlay
            and s.contains("geometry/view_toolbar")
        ):
            self.win.view._overlay.setGeometry(s.value("geometry/view_toolbar"))
        if (
            hasattr(self.win.view, "_main_tools_overlay")
            and self.win.view._main_tools_overlay
            and s.contains("geometry/main_toolbar")
        ):
            self.win.view._main_tools_overlay.setGeometry(
                s.value("geometry/main_toolbar")
            )

        # Ensure toolbars are always on top
        if hasattr(self.win.view, "_overlay") and self.win.view._overlay:
            self.win.view._overlay.raise_()
        if (
            hasattr(self.win.view, "_main_tools_overlay")
            and self.win.view._main_tools_overlay
        ):
            self.win.view._main_tools_overlay.raise_()

        self._load_shortcuts()

    def _load_shortcuts(self) -> None:
        """Loads the keyboard shortcuts from settings."""
        if not hasattr(self.win, "shortcuts"):
            return
        s = QSettings(self.org, self.app)
        s.beginGroup("shortcuts")
        for key, action in self.win.shortcuts.items():
            seq = s.value(key)
            if seq:
                action.setShortcut(seq)
        s.endGroup()

    def clear(self) -> None:
        """Clears all application settings."""
        s = QSettings(self.org, self.app)
        # Only clear geometry/layout; keep theme, icons, overlays builder, timeline colors
        for key in [
            "geometry/mainwindow",
            "geometry/library",
            "geometry/inspector",
            "geometry/view_toolbar",
            "geometry/main_toolbar",
            "layout/timeline_visible",
        ]:
            s.remove(key)

    def open_dialog(self) -> None:
        """Opens the settings dialog and applies the changes if accepted."""
        from ui.settings_dialog import SettingsDialog

        win = self.win
        dlg = SettingsDialog(win)
        if hasattr(win, "shortcuts"):
            dlg.set_shortcut_actions(win.shortcuts)

        s = QSettings(self.org, self.app)
        icon_dir = s.value("ui/icon_dir")
        if icon_dir:
            try:
                dlg.icon_dir_edit.setText(str(icon_dir))
            except (RuntimeError, AttributeError):
                logging.exception("Failed to set icon directory text")
        try:
            dlg.icon_size_spin.setValue(int(s.value("ui/icon_size", 32)))
        except (TypeError, ValueError):
            dlg.icon_size_spin.setValue(32)
        theme = str(s.value("ui/theme", "dark")).lower()
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

                theme_path = s.value("ui/theme_file") or str(
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
                s.beginGroup("ui/custom_params")

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
                            int(float(s.value("panel_opacity", 0.9)) * 100)
                        )
                    except Exception:
                        dlg.opacity_spin.setValue(90)
                    dlg.radius_spin.setValue(int(s.value("radius", 12) or 12))
                    dlg.font_spin.setValue(int(s.value("font_size", 10) or 10))
                    dlg.font_family_edit.setText(
                        _gv("font_family", str(s.value("ui/font_family") or "Poppins"))
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
                fam = s.value("ui/font_family") or "Poppins"
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

        # Menu builder defaults
        def getb(key: str, default: bool = True) -> bool:
            v = s.value(key)
            return default if v is None else (v in [True, "true", "1"])

        dlg.cb_custom_visible.setChecked(getb("ui/menu/custom/visible", False))

        # Populate icon lists with order + visibility
        def get_order_and_vis(
            prefix: str, default_order: list[str]
        ) -> tuple[list[str], dict[str, bool]]:
            order = s.value(f"ui/menu/{prefix}/order") or default_order
            if isinstance(order, str):
                order = [k for k in order.split(",") if k]
            vis: dict[str, bool] = {}
            for k in order:
                v = s.value(f"ui/menu/{prefix}/{k}")
                vis[k] = True if v is None else (v in [True, "true", "1"])
            return order, vis

        from ui.menu_defaults import (
            MAIN_DEFAULT_ORDER,
            QUICK_DEFAULT_ORDER,
            CUSTOM_DEFAULT_ORDER,
        )

        main_default = list(MAIN_DEFAULT_ORDER)
        quick_default = list(QUICK_DEFAULT_ORDER)
        custom_default = list(CUSTOM_DEFAULT_ORDER)
        main_order, main_vis = get_order_and_vis("main", main_default)
        quick_order, quick_vis = get_order_and_vis("quick", quick_default)
        custom_order, custom_vis = get_order_and_vis("custom", custom_default)
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
                dlg.icon_norm_edit.setText(
                    str(s_ic.value("ui/icon_color_normal") or "#4A5568")
                )
                dlg.icon_hover_edit.setText(
                    str(s_ic.value("ui/icon_color_hover") or "#E53E3E")
                )
                dlg.icon_active_edit.setText(
                    str(s_ic.value("ui/icon_color_active") or "#FFFFFF")
                )
        except Exception:
            logging.exception("Failed to preload icon colors")

        # Preload timeline colors
        try:
            dlg.tl_bg.setText(str(s.value("timeline/bg") or "#1E1E1E"))
            dlg.tl_ruler_bg.setText(str(s.value("timeline/ruler_bg") or "#2C2C2C"))
            dlg.tl_track_bg.setText(str(s.value("timeline/track_bg") or "#242424"))
            dlg.tl_tick.setText(str(s.value("timeline/tick") or "#8A8A8A"))
            dlg.tl_tick_major.setText(str(s.value("timeline/tick_major") or "#E0E0E0"))
            dlg.tl_playhead.setText(str(s.value("timeline/playhead") or "#65B0FF"))
            dlg.tl_kf.setText(str(s.value("timeline/kf") or "#FFC107"))
            dlg.tl_kf_hover.setText(str(s.value("timeline/kf_hover") or "#FFE082"))
            try:
                dlg.tl_inout_alpha.setValue(int(s.value("timeline/inout_alpha", 30)))
            except Exception:
                dlg.tl_inout_alpha.setValue(30)
        except Exception:
            logging.exception("Failed to preload timeline colors")

        # Preload scene background color
        try:
            dlg.scene_bg_edit.setText(str(s.value("ui/style/scene_bg") or ""))
        except Exception:
            logging.exception("Failed to preload scene background color")

        # Onion values
        try:
            dlg.prev_count.setValue(int(s.value("onion/prev_count", 2)))
            dlg.next_count.setValue(int(s.value("onion/next_count", 1)))
            dlg.opacity_prev.setValue(float(s.value("onion/opacity_prev", 0.25)))
            dlg.opacity_next.setValue(float(s.value("onion/opacity_next", 0.18)))
        except (ValueError, TypeError):
            logging.exception("Failed to load onion settings")

        # Apply button: apply without closing
        def _apply_all() -> None:
            try:
                # icon dir / size
                icon_dir = dlg.icon_dir_edit.text().strip()
                s.setValue("ui/icon_dir", icon_dir if icon_dir else "")
                s.setValue("ui/icon_size", int(dlg.icon_size_spin.value()))
                # font family
                s.setValue(
                    "ui/font_family", dlg.font_family_edit.text().strip() or "Poppins"
                )
                # theme
                theme = dlg.preset_combo.currentText().strip().lower() or "light"
                s.setValue("ui/theme", theme)
                if theme == "custom":
                    params = {
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
                        # Inputs/lists/checkboxes exposés
                        "input_bg": dlg.input_bg_edit.text() or "#EDF2F7",
                        "input_border": dlg.input_border_edit.text() or "#CBD5E0",
                        "input_text": dlg.input_text_edit.text()
                        or (dlg.text_edit.text() or "#1A202C"),
                        "input_focus_bg": dlg.input_focus_bg_edit.text() or "#FFFFFF",
                        "input_focus_border": dlg.input_focus_border_edit.text()
                        or (dlg.accent_edit.text() or "#E53E3E"),
                        "list_hover_bg": dlg.list_hover_edit.text() or "#E2E8F0",
                        "list_selected_bg": dlg.list_sel_bg_edit.text()
                        or (dlg.accent_edit.text() or "#E53E3E"),
                        "list_selected_text": dlg.list_sel_text_edit.text()
                        or "#FFFFFF",
                        "checkbox_unchecked_bg": dlg.cb_un_bg_edit.text() or "#EDF2F7",
                        "checkbox_unchecked_border": dlg.cb_un_border_edit.text()
                        or "#A0AEC0",
                        "checkbox_checked_bg": dlg.cb_ch_bg_edit.text()
                        or (dlg.accent_edit.text() or "#E53E3E"),
                        "checkbox_checked_border": dlg.cb_ch_border_edit.text()
                        or "#C53030",
                        "checkbox_checked_hover": dlg.cb_ch_hover_edit.text()
                        or "#F56565",
                    }
                    css = build_stylesheet(params)
                    s.setValue("ui/custom_stylesheet", css)
                    # Save to theme file for persistence beyond resets
                    from pathlib import Path

                    theme_path = s.value("ui/theme_file") or str(
                        Path.home() / ".config/JaJa/Macronotron/theme.json"
                    )
                    try:
                        p = Path(str(theme_path))
                        p.parent.mkdir(parents=True, exist_ok=True)
                        import json

                        p.write_text(json.dumps(params, indent=2), encoding="utf-8")
                        s.setValue("ui/theme_file", str(p))
                    except Exception:
                        logging.exception("Failed to write theme file")
                    # Keep QSettings copy for compatibility
                    s.beginGroup("ui/custom_params")
                    for k, v in params.items():
                        s.setValue(k, v)
                    s.endGroup()
                # scene bg
                scene_bg = dlg.scene_bg_edit.text().strip()
                s.setValue("ui/style/scene_bg", scene_bg)
                if scene_bg:
                    from PySide6.QtGui import QColor

                    self.win.scene.setBackgroundBrush(QColor(scene_bg))
                    self.win.view.viewport().update()
                # icon colors
                if hasattr(dlg, "icon_norm_edit"):
                    s.setValue(
                        "ui/icon_color_normal",
                        dlg.icon_norm_edit.text().strip() or "#4A5568",
                    )
                    s.setValue(
                        "ui/icon_color_hover",
                        dlg.icon_hover_edit.text().strip() or "#E53E3E",
                    )
                    s.setValue(
                        "ui/icon_color_active",
                        dlg.icon_active_edit.text().strip() or "#FFFFFF",
                    )
                # timeline colors
                s.setValue("timeline/bg", dlg.tl_bg.text().strip() or "#1E1E1E")
                s.setValue(
                    "timeline/ruler_bg", dlg.tl_ruler_bg.text().strip() or "#2C2C2C"
                )
                s.setValue(
                    "timeline/track_bg", dlg.tl_track_bg.text().strip() or "#242424"
                )
                s.setValue("timeline/tick", dlg.tl_tick.text().strip() or "#8A8A8A")
                s.setValue(
                    "timeline/tick_major", dlg.tl_tick_major.text().strip() or "#E0E0E0"
                )
                s.setValue(
                    "timeline/playhead", dlg.tl_playhead.text().strip() or "#65B0FF"
                )
                s.setValue("timeline/kf", dlg.tl_kf.text().strip() or "#FFC107")
                s.setValue(
                    "timeline/kf_hover", dlg.tl_kf_hover.text().strip() or "#FFE082"
                )
                s.setValue("timeline/inout_alpha", int(dlg.tl_inout_alpha.value()))
                # Refresh
                from ui import icons as app_icons
                from ui.icons import (
                    icon_save,
                    icon_open,
                    icon_scene_size,
                    icon_background,
                    icon_reset_scene,
                    icon_reset_ui,
                    icon_library,
                    icon_inspector,
                    icon_timeline,
                )

                app_icons.clear_cache()
                self.win.save_action.setIcon(icon_save())
                self.win.load_action.setIcon(icon_open())
                self.win.scene_size_action.setIcon(icon_scene_size())
                self.win.background_action.setIcon(icon_background())
                self.win.reset_scene_action.setIcon(icon_reset_scene())
                self.win.reset_ui_action.setIcon(icon_reset_ui())
                self.win.toggle_library_action.setIcon(icon_library())
                self.win.toggle_inspector_action.setIcon(icon_inspector())
                self.win.timeline_dock.toggleViewAction().setIcon(icon_timeline())
                self.win.view.refresh_overlay_icons(self.win)
                self.win.view.apply_menu_settings_main()
                self.win.view.apply_menu_settings_quick()
                self.win.timeline_widget.update()
                apply_stylesheet(QApplication.instance(), load_active_profile())
            except Exception:
                logging.exception("Apply settings failed")

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
            dlg.btn_export_profile.clicked.connect(_export_profile)
            dlg.btn_import_profile.clicked.connect(_import_profile)
            dlg.btn_reset_profile.clicked.connect(_reset_profile_default)
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
                apply_stylesheet(QApplication.instance(), prof)
            except Exception:
                logging.exception("Failed to persist UIProfile from dialog")
