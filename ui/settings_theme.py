from __future__ import annotations

"""Theme-related helpers for SettingsManager."""

import logging
from typing import Any

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

import ui.icons as app_icons
from ui.styles import apply_stylesheet, build_stylesheet
from ui.ui_profile import _bool


def get_bool_setting(s: QSettings, key: str, default: bool = True) -> bool:
    """Return a normalized boolean from QSettings."""
    try:
        return _bool(s.value(key), default)
    except Exception:
        logging.debug("get_bool_setting fallback for %s", key)
        return default


def get_order_and_vis(
    s: QSettings, prefix: str, default_order: list[str]
) -> tuple[list[str], dict[str, bool]]:
    """Read order and visibility map for a menu prefix from QSettings."""
    from ui.settings_keys import UI_MENU_ORDER, UI_MENU_VIS

    order: list[str] | str | None = s.value(UI_MENU_ORDER(prefix))
    if not order:
        order_list = list(default_order)
    elif isinstance(order, str):
        order_list = [k for k in order.split(",") if k]
    else:
        order_list = list(order)  # type: ignore[arg-type]
    vis: dict[str, bool] = {}
    for k in order_list:
        v = s.value(UI_MENU_VIS(prefix, k))
        vis[k] = _bool(v, True)
    return order_list, vis


def apply_all_settings(win: Any, dlg: Any, s: QSettings) -> None:
    """Apply settings from the dialog widgets into QSettings and refresh UI."""
    try:
        from ui.settings_keys import (
            UI_ICON_DIR,
            UI_ICON_SIZE,
            UI_FONT_FAMILY,
            UI_THEME,
            UI_CUSTOM_STYLESHEET,
            UI_THEME_FILE,
            UI_CUSTOM_PARAMS_GROUP,
            UI_STYLE_SCENE_BG,
            UI_ICON_COLOR_NORMAL,
            UI_ICON_COLOR_HOVER,
            UI_ICON_COLOR_ACTIVE,
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

        icon_dir = dlg.icon_dir_edit.text().strip()
        s.setValue(UI_ICON_DIR, icon_dir if icon_dir else "")
        s.setValue(UI_ICON_SIZE, int(dlg.icon_size_spin.value()))
        s.setValue(UI_FONT_FAMILY, dlg.font_family_edit.text().strip() or "Poppins")
        theme = dlg.preset_combo.currentText().strip().lower() or "light"
        s.setValue(UI_THEME, theme)
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
                # Inputs/lists/checkboxes
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
                "list_selected_text": dlg.list_sel_text_edit.text() or "#FFFFFF",
                "checkbox_unchecked_bg": dlg.cb_un_bg_edit.text() or "#EDF2F7",
                "checkbox_unchecked_border": dlg.cb_un_border_edit.text() or "#A0AEC0",
                "checkbox_checked_bg": dlg.cb_ch_bg_edit.text()
                or (dlg.accent_edit.text() or "#E53E3E"),
                "checkbox_checked_border": dlg.cb_ch_border_edit.text() or "#C53030",
                "checkbox_checked_hover": dlg.cb_ch_hover_edit.text() or "#F56565",
            }
            css = build_stylesheet(params)
            s.setValue(UI_CUSTOM_STYLESHEET, css)
            from pathlib import Path

            try:
                theme_path = s.value(UI_THEME_FILE) or str(
                    Path.home() / ".config/JaJa/Macronotron/theme.json"
                )
                p = Path(str(theme_path))
                p.parent.mkdir(parents=True, exist_ok=True)
                import json

                p.write_text(json.dumps(params, indent=2), encoding="utf-8")
                s.setValue(UI_THEME_FILE, str(p))
            except Exception:
                logging.exception("Failed to write theme file")
            s.beginGroup(UI_CUSTOM_PARAMS_GROUP)
            for k, v in params.items():
                s.setValue(k, v)
            s.endGroup()
        scene_bg = dlg.scene_bg_edit.text().strip()
        s.setValue(UI_STYLE_SCENE_BG, scene_bg)
        if scene_bg:
            from PySide6.QtGui import QColor

            win.scene.setBackgroundBrush(QColor(scene_bg))
            win.view.viewport().update()
        if hasattr(dlg, "icon_norm_edit"):
            s.setValue(
                UI_ICON_COLOR_NORMAL, dlg.icon_norm_edit.text().strip() or "#4A5568"
            )
            s.setValue(
                UI_ICON_COLOR_HOVER, dlg.icon_hover_edit.text().strip() or "#E53E3E"
            )
            s.setValue(
                UI_ICON_COLOR_ACTIVE, dlg.icon_active_edit.text().strip() or "#FFFFFF"
            )
        s.setValue(TIMELINE_BG, dlg.tl_bg.text().strip() or "#1E1E1E")
        s.setValue(TIMELINE_RULER_BG, dlg.tl_ruler_bg.text().strip() or "#2C2C2C")
        s.setValue(TIMELINE_TRACK_BG, dlg.tl_track_bg.text().strip() or "#242424")
        s.setValue(TIMELINE_TICK, dlg.tl_tick.text().strip() or "#8A8A8A")
        s.setValue(TIMELINE_TICK_MAJOR, dlg.tl_tick_major.text().strip() or "#E0E0E0")
        s.setValue(TIMELINE_PLAYHEAD, dlg.tl_playhead.text().strip() or "#65B0FF")
        s.setValue(TIMELINE_KF, dlg.tl_kf.text().strip() or "#FFC107")
        s.setValue(TIMELINE_KF_HOVER, dlg.tl_kf_hover.text().strip() or "#FFE082")
        s.setValue(TIMELINE_INOUT_ALPHA, int(dlg.tl_inout_alpha.value()))
        try:
            app_icons.clear_cache()
            win.save_action.setIcon(app_icons.get_icon("save"))
            win.load_action.setIcon(app_icons.get_icon("open"))
            win.scene_size_action.setIcon(app_icons.get_icon("scene_size"))
            win.background_action.setIcon(app_icons.get_icon("background"))
            win.reset_scene_action.setIcon(app_icons.get_icon("new_file"))
            win.reset_ui_action.setIcon(app_icons.get_icon("reset_ui"))
            win.toggle_library_action.setIcon(app_icons.get_icon("library"))
            win.toggle_inspector_action.setIcon(app_icons.get_icon("inspector"))
            win.timeline_dock.toggleViewAction().setIcon(app_icons.get_icon("timeline"))
            win.view.refresh_overlay_icons(win)
            win.view.apply_menu_settings_main()
            win.view.apply_menu_settings_quick()
            win.timeline_widget.update()
        except Exception:
            logging.exception("Failed to refresh icons after applying settings")
        apply_stylesheet(QApplication.instance())
    except Exception:
        logging.exception("Apply settings failed")
