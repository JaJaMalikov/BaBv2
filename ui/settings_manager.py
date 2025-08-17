'''Module for managing application settings, including UI layout and theme.'''

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QPoint, QSettings, QSize
from PySide6.QtWidgets import QApplication

import ui.icons as app_icons
from ui.icons import (
    icon_background,
    icon_inspector,
    icon_library,
    icon_open,
    icon_reset_scene,
    icon_reset_ui,
    icon_save,
    icon_scene_size,
    icon_timeline,
)
from ui.styles import apply_stylesheet, build_stylesheet


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
        theme = str(s.value("ui/theme", "light")).lower()
        try:
            presets_map = {"light": "Light", "dark": "Dark", "high contrast": "High Contrast", "custom": "Custom"}
            dlg.preset_combo.setCurrentText(presets_map.get(theme, "Light"))
            if theme == "custom":
                # Load from theme file if present, else from custom_params
                from pathlib import Path
                theme_path = s.value("ui/theme_file") or str(Path.home() / ".config/JaJa/Macronotron/theme.json")
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
                    dlg.tooltip_bg_edit.setText(_gv("tooltip_bg", dlg.panel_edit.text()))
                    dlg.tooltip_text_edit.setText(_gv("tooltip_text", dlg.text_edit.text()))
                    # Numeric params
                    try:
                        dlg.opacity_spin.setValue(int(float(s.value("panel_opacity", 0.9)) * 100))
                    except Exception:
                        dlg.opacity_spin.setValue(90)
                    dlg.radius_spin.setValue(int(s.value("radius", 12) or 12))
                    dlg.font_spin.setValue(int(s.value("font_size", 10) or 10))
                    dlg.font_family_edit.setText(_gv("font_family", str(s.value("ui/font_family") or "Poppins")))
                except Exception:
                    logging.exception("Failed to load custom params")
                finally:
                    s.endGroup()
                try:
                    dlg._update_all_swatches(); dlg._preview_theme()
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

        main_default = [
            "save",
            "load",
            "scene_size",
            "background",
            "settings",
            "reset_scene",
            "reset_ui",
            "toggle_library",
            "toggle_inspector",
            "toggle_timeline",
            "toggle_custom",
        ]
        quick_default = ["zoom_out", "zoom_in", "fit", "handles", "onion"]
        custom_default = [
            "save",
            "load",
            "scene_size",
            "background",
            "settings",
            "zoom_out",
            "zoom_in",
            "fit",
            "handles",
            "onion",
        ]
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
            if hasattr(dlg, 'icon_norm_edit'):
                s_ic = QSettings(self.org, self.app)
                dlg.icon_norm_edit.setText(str(s_ic.value("ui/icon_color_normal") or "#4A5568"))
                dlg.icon_hover_edit.setText(str(s_ic.value("ui/icon_color_hover") or "#E53E3E"))
                dlg.icon_active_edit.setText(str(s_ic.value("ui/icon_color_active") or "#FFFFFF"))
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
                s.setValue("ui/font_family", dlg.font_family_edit.text().strip() or "Poppins")
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
                        "header_text": dlg.header_text_edit.text() or dlg.text_edit.text() or "#1A202C",
                        "header_border": dlg.header_border_edit.text() or dlg.border_edit.text() or "#D0D5DD",
                        "group_title_color": dlg.group_edit.text() or "#2D3748",
                        "tooltip_bg": dlg.tooltip_bg_edit.text() or "#F7F8FC",
                        "tooltip_text": dlg.tooltip_text_edit.text() or "#1A202C",
                        "tooltip_border": dlg.border_edit.text() or "#D0D5DD",
                        "radius": dlg.radius_spin.value(),
                        "font_size": dlg.font_spin.value(),
                        "font_family": dlg.font_family_edit.text() or "Poppins",
                    }
                    css = build_stylesheet(params)
                    s.setValue("ui/custom_stylesheet", css)
                    # Save to theme file for persistence beyond resets
                    from pathlib import Path
                    theme_path = s.value("ui/theme_file") or str(Path.home() / ".config/JaJa/Macronotron/theme.json")
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
                if hasattr(dlg, 'icon_norm_edit'):
                    s.setValue("ui/icon_color_normal", dlg.icon_norm_edit.text().strip() or "#4A5568")
                    s.setValue("ui/icon_color_hover", dlg.icon_hover_edit.text().strip() or "#E53E3E")
                    s.setValue("ui/icon_color_active", dlg.icon_active_edit.text().strip() or "#FFFFFF")
                # timeline colors
                s.setValue("timeline/bg", dlg.tl_bg.text().strip() or "#1E1E1E")
                s.setValue("timeline/ruler_bg", dlg.tl_ruler_bg.text().strip() or "#2C2C2C")
                s.setValue("timeline/track_bg", dlg.tl_track_bg.text().strip() or "#242424")
                s.setValue("timeline/tick", dlg.tl_tick.text().strip() or "#8A8A8A")
                s.setValue("timeline/tick_major", dlg.tl_tick_major.text().strip() or "#E0E0E0")
                s.setValue("timeline/playhead", dlg.tl_playhead.text().strip() or "#65B0FF")
                s.setValue("timeline/kf", dlg.tl_kf.text().strip() or "#FFC107")
                s.setValue("timeline/kf_hover", dlg.tl_kf_hover.text().strip() or "#FFE082")
                s.setValue("timeline/inout_alpha", int(dlg.tl_inout_alpha.value()))
                # Refresh
                from ui import icons as app_icons
                from ui.icons import icon_save, icon_open, icon_scene_size, icon_background, icon_reset_scene, icon_reset_ui, icon_library, icon_inspector, icon_timeline
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
                apply_stylesheet(QApplication.instance())
            except Exception:
                logging.exception("Apply settings failed")

        try:
            dlg.btn_apply.clicked.connect(_apply_all)
        except Exception:
            logging.exception("Failed to connect Apply button")

        # Autosave on change: Styles (when Custom) and Timeline pickers
        def _maybe_autosave_styles() -> None:
            try:
                if dlg.preset_combo.currentText().strip().lower() == "custom":
                    _apply_all()
            except Exception:
                logging.exception("Autosave styles failed")

        def _autosave_timeline() -> None:
            try:
                # Save only the timeline keys, then update widget (cheaper than full apply)
                s.setValue("timeline/bg", dlg.tl_bg.text().strip())
                s.setValue("timeline/ruler_bg", dlg.tl_ruler_bg.text().strip())
                s.setValue("timeline/track_bg", dlg.tl_track_bg.text().strip())
                s.setValue("timeline/tick", dlg.tl_tick.text().strip())
                s.setValue("timeline/tick_major", dlg.tl_tick_major.text().strip())
                s.setValue("timeline/playhead", dlg.tl_playhead.text().strip())
                s.setValue("timeline/kf", dlg.tl_kf.text().strip())
                s.setValue("timeline/kf_hover", dlg.tl_kf_hover.text().strip())
                s.setValue("timeline/inout_alpha", int(dlg.tl_inout_alpha.value()))
                self.win.timeline_widget.update()
            except Exception:
                logging.exception("Autosave timeline failed")

        try:
            # Styles autosave signals
            for e in [
                dlg.bg_edit, dlg.text_edit, dlg.accent_edit, dlg.hover_edit,
                dlg.panel_edit, dlg.border_edit, dlg.header_bg_edit, dlg.header_text_edit,
                dlg.header_border_edit, dlg.tooltip_bg_edit, dlg.tooltip_text_edit,
                dlg.group_edit, dlg.font_family_edit,
            ]:
                e.textChanged.connect(_maybe_autosave_styles)
            for sp in [dlg.opacity_spin, dlg.radius_spin, dlg.font_spin]:
                sp.valueChanged.connect(lambda _=None: _maybe_autosave_styles())
            dlg.scene_bg_edit.textChanged.connect(_maybe_autosave_styles)
            dlg.preset_combo.currentTextChanged.connect(lambda _=None: _maybe_autosave_styles())

            # Timeline autosave signals
            for e in [
                dlg.tl_bg, dlg.tl_ruler_bg, dlg.tl_track_bg, dlg.tl_tick,
                dlg.tl_tick_major, dlg.tl_playhead, dlg.tl_kf, dlg.tl_kf_hover,
            ]:
                e.textChanged.connect(_autosave_timeline)
            dlg.tl_inout_alpha.valueChanged.connect(lambda _=None: _autosave_timeline())
        except Exception:
            logging.exception("Failed to wire autosave signals")

        if dlg.exec() == SettingsDialog.Accepted:
            _apply_all()
            if hasattr(win, "shortcuts"):
                s.beginGroup("shortcuts")
                for key, seq in dlg.get_shortcuts().items():
                    s.setValue(key, seq)
                    win.shortcuts[key].setShortcut(seq)
                s.endGroup()

            # UI: icon directory and default overlay sizes
            icon_dir = dlg.icon_dir_edit.text().strip()
            s.setValue("ui/icon_dir", icon_dir if icon_dir else "")
            s.setValue("ui/icon_size", int(dlg.icon_size_spin.value()))
            # Save font family for global app font
            s.setValue("ui/font_family", dlg.font_family_edit.text().strip() or "Poppins")
            theme = dlg.preset_combo.currentText().strip().lower() or "light"
            s.setValue("ui/theme", theme)
            if theme == "custom":
                try:
                    params = {
                        "bg_color": dlg.bg_edit.text() or "#E2E8F0",
                        "text_color": dlg.text_edit.text() or "#1A202C",
                        "accent_color": dlg.accent_edit.text() or "#E53E3E",
                        "hover_color": dlg.hover_edit.text() or "#E3E6FD",
                        "panel_bg": dlg.panel_edit.text() or "#F7F8FC",
                        "panel_opacity": (dlg.opacity_spin.value() / 100.0),
                        "panel_border": dlg.border_edit.text() or "#D0D5DD",
                        "header_bg": dlg.header_bg_edit.text() or "",
                        "header_text": dlg.header_text_edit.text() or dlg.text_edit.text() or "#1A202C",
                        "header_border": dlg.header_border_edit.text() or dlg.border_edit.text() or "#D0D5DD",
                        "group_title_color": dlg.group_edit.text() or "#2D3748",
                        "tooltip_bg": dlg.tooltip_bg_edit.text() or "#F7F8FC",
                        "tooltip_text": dlg.tooltip_text_edit.text() or "#1A202C",
                        "tooltip_border": dlg.border_edit.text() or "#D0D5DD",
                        "radius": dlg.radius_spin.value(),
                        "font_size": dlg.font_spin.value(),
                        "font_family": dlg.font_family_edit.text() or "Poppins",
                    }
                    css = build_stylesheet(params)
                    s.setValue("ui/custom_stylesheet", css)
                    # Persist individual params for next open
                    s.beginGroup("ui/custom_params")
                    for k, v in params.items():
                        s.setValue(k, v)
                    s.endGroup()
                except (RuntimeError, ImportError, ValueError):
                    logging.exception("Failed to build custom stylesheet")
            # Default sizes/positions
            s.setValue(
                "ui/default/library_size",
                QSize(max(150, dlg.lib_w.value()), max(150, dlg.lib_h.value())),
            )
            s.setValue(
                "ui/default/inspector_size",
                QSize(max(150, dlg.insp_w.value()), max(150, dlg.insp_h.value())),
            )
            s.setValue(
                "ui/default/library_pos",
                QPoint(max(0, dlg.lib_x.value()), max(0, dlg.lib_y.value())),
            )
            s.setValue(
                "ui/default/inspector_pos",
                QPoint(max(0, dlg.insp_x.value()), max(0, dlg.insp_y.value())),
            )
            s.setValue(
                "ui/default/custom_pos",
                QPoint(max(0, dlg.cust_x.value()), max(0, dlg.cust_y.value())),
            )
            s.setValue(
                "ui/default/custom_size",
                QSize(max(100, dlg.cust_w.value()), max(60, dlg.cust_h.value())),
            )
            # Apply immediate size/pos changes
            try:
                if dlg.lib_w.value() and dlg.lib_h.value():
                    win.library_overlay.resize(dlg.lib_w.value(), dlg.lib_h.value())
                if dlg.insp_w.value() and dlg.insp_h.value():
                    win.inspector_overlay.resize(
                        dlg.insp_w.value(), dlg.insp_h.value()
                    )
                win.library_overlay.move(max(0, dlg.lib_x.value()), max(0, dlg.lib_y.value()))
                win.inspector_overlay.move(
                    max(0, dlg.insp_x.value()), max(0, dlg.insp_y.value())
                )
                cust = getattr(win.view, "_custom_tools_overlay", None)
                if cust is not None:
                    cust.resize(max(100, dlg.cust_w.value()), max(60, dlg.cust_h.value()))
                    cust.move(max(0, dlg.cust_x.value()), max(0, dlg.cust_y.value()))
            except (RuntimeError, AttributeError):
                logging.exception("Failed to apply overlay geometry")

            # Custom overlay visibility
            s.setValue("ui/menu/custom/visible", dlg.cb_custom_visible.isChecked())

            # Scene background color (no image)
            scene_bg = dlg.scene_bg_edit.text().strip()
            s.setValue("ui/style/scene_bg", scene_bg)
            try:
                if scene_bg:
                    from PySide6.QtGui import QColor
                    win.scene.setBackgroundBrush(QColor(scene_bg))
                    win.view.viewport().update()
            except Exception:
                logging.exception("Failed to apply scene background brush")

            # Orders and visibility
            main_order, main_vis = dlg.extract_icon_list(dlg.list_main_order)
            quick_order, quick_vis = dlg.extract_icon_list(dlg.list_quick_order)
            custom_order, custom_vis = dlg.extract_icon_list(dlg.list_custom_order)
            s.setValue("ui/menu/main/order", main_order)
            s.setValue("ui/menu/quick/order", quick_order)
            s.setValue("ui/menu/custom/order", custom_order)
            for k, v in main_vis.items():
                s.setValue(f"ui/menu/main/{k}", v)
            for k, v in quick_vis.items():
                s.setValue(f"ui/menu/quick/{k}", v)
            for k, v in custom_vis.items():
                s.setValue(f"ui/menu/custom/{k}", v)

            # Timeline colors
            try:
                s.setValue("timeline/bg", dlg.tl_bg.text().strip() or "#1E1E1E")
                s.setValue("timeline/ruler_bg", dlg.tl_ruler_bg.text().strip() or "#2C2C2C")
                s.setValue("timeline/track_bg", dlg.tl_track_bg.text().strip() or "#242424")
                s.setValue("timeline/tick", dlg.tl_tick.text().strip() or "#8A8A8A")
                s.setValue("timeline/tick_major", dlg.tl_tick_major.text().strip() or "#E0E0E0")
                s.setValue("timeline/playhead", dlg.tl_playhead.text().strip() or "#65B0FF")
                s.setValue("timeline/kf", dlg.tl_kf.text().strip() or "#FFC107")
                s.setValue("timeline/kf_hover", dlg.tl_kf_hover.text().strip() or "#FFE082")
                s.setValue("timeline/inout_alpha", int(dlg.tl_inout_alpha.value()))
                win.timeline_widget.update()
            except Exception:
                logging.exception("Failed to save timeline colors")

            # Onion persisted and applied
            s.setValue("onion/prev_count", int(dlg.prev_count.value()))
            s.setValue("onion/next_count", int(dlg.next_count.value()))
            s.setValue("onion/opacity_prev", float(dlg.opacity_prev.value()))
            s.setValue("onion/opacity_next", float(dlg.opacity_next.value()))
            try:
                win.onion.prev_count = int(dlg.prev_count.value())
                win.onion.next_count = int(dlg.next_count.value())
                win.onion.opacity_prev = float(dlg.opacity_prev.value())
                win.onion.opacity_next = float(dlg.opacity_next.value())
                win.update_onion_skins()
            except (RuntimeError, ValueError):
                logging.exception("Failed to apply onion settings")

            # Refresh icons everywhere and apply scene background if requested
            try:
                app_icons.clear_cache()
                # Persist icon colors explicitly (allow full control)
                if hasattr(dlg, 'icon_norm_edit'):
                    s.setValue("ui/icon_color_normal", dlg.icon_norm_edit.text().strip() or "#4A5568")
                    s.setValue("ui/icon_color_hover", dlg.icon_hover_edit.text().strip() or "#E53E3E")
                    s.setValue("ui/icon_color_active", dlg.icon_active_edit.text().strip() or "#FFFFFF")
                else:
                    s.setValue("ui/icon_color_normal", dlg.text_edit.text() or "#4A5568")
                    s.setValue("ui/icon_color_hover", dlg.accent_edit.text() or "#E53E3E")
                    s.setValue("ui/icon_color_active", "#FFFFFF")
                win.save_action.setIcon(icon_save())
                win.load_action.setIcon(icon_open())
                win.scene_size_action.setIcon(icon_scene_size())
                win.background_action.setIcon(icon_background())
                win.reset_scene_action.setIcon(icon_reset_scene())
                win.reset_ui_action.setIcon(icon_reset_ui())
                win.toggle_library_action.setIcon(icon_library())
                win.toggle_inspector_action.setIcon(icon_inspector())
                win.timeline_dock.toggleViewAction().setIcon(icon_timeline())
                win.view.refresh_overlay_icons(win)
                win.view.apply_menu_settings_main()
                win.view.apply_menu_settings_quick()
                try:
                    win.view._build_custom_tools_overlay(win)
                except RuntimeError:
                    logging.exception("Failed to build custom tools overlay")
                win.set_custom_overlay_visible(
                    bool(s.value("ui/menu/custom/visible") in [True, "true", "1"])
                )
                # Optional scene background color (not the image)
                scene_bg = s.value("ui/style/scene_bg")
                if scene_bg:
                    from PySide6.QtGui import QColor
                    try:
                        win.scene.setBackgroundBrush(QColor(str(scene_bg)))
                        win.view.viewport().update()
                    except Exception:
                        logging.exception("Failed to apply scene background brush")
            except (RuntimeError, ImportError, AttributeError):
                logging.exception("Failed to refresh icons globally")

            # Apply theme immediately
            try:
                apply_stylesheet(QApplication.instance())
            except Exception:
                logging.exception("Failed to apply stylesheet immediately; falling back to light theme")
