from __future__ import annotations

from typing import Any
from PySide6.QtCore import QSettings, QSize, QPoint
from PySide6.QtWidgets import QApplication

from ui.settings_dialog import SettingsDialog
from ui.styles import apply_stylesheet
from ui.icons import (
    icon_scene_size, icon_background, icon_library, icon_inspector, icon_timeline,
    icon_save, icon_open, icon_reset_ui, icon_reset_scene
)


class SettingsManager:
    """Encapsule l'enregistrement et la restauration des réglages UI (géométries, visibilité)."""

    def __init__(self, win: Any) -> None:
        self.win = win
        self.org = "JaJa"
        self.app = "Macronotron"

    def save(self) -> None:
        s = QSettings(self.org, self.app)
        s.setValue("geometry/mainwindow", self.win.saveGeometry())
        s.setValue("geometry/library", self.win.library_overlay.geometry())
        s.setValue("geometry/inspector", self.win.inspector_overlay.geometry())
        s.setValue("layout/timeline_visible", self.win.timeline_dock.isVisible())
        if hasattr(self.win.view, '_overlay') and self.win.view._overlay:
            s.setValue("geometry/view_toolbar", self.win.view._overlay.geometry())
        if hasattr(self.win.view, '_main_tools_overlay') and self.win.view._main_tools_overlay:
            s.setValue("geometry/main_toolbar", self.win.view._main_tools_overlay.geometry())

    def load(self) -> None:
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
            self.win.timeline_dock.setVisible(is_visible in [True, 'true'])
        if hasattr(self.win.view, '_overlay') and self.win.view._overlay and s.contains("geometry/view_toolbar"):
            self.win.view._overlay.setGeometry(s.value("geometry/view_toolbar"))
        if hasattr(self.win.view, '_main_tools_overlay') and self.win.view._main_tools_overlay and s.contains("geometry/main_toolbar"):
            self.win.view._main_tools_overlay.setGeometry(s.value("geometry/main_toolbar"))

        # Ensure toolbars are always on top
        if hasattr(self.win.view, '_overlay') and self.win.view._overlay:
            self.win.view._overlay.raise_()
        if hasattr(self.win.view, '_main_tools_overlay') and self.win.view._main_tools_overlay:
            self.win.view._main_tools_overlay.raise_()

    def clear(self) -> None:
        s = QSettings(self.org, self.app)
        s.clear()

    # --- Settings Dialog orchestration moved from MainWindow ---
    def open_dialog(self) -> None:
        win = self.win
        dlg = SettingsDialog(win)

        s = QSettings(self.org, self.app)
        icon_dir = s.value("ui/icon_dir")
        if icon_dir:
            try:
                dlg.icon_dir_edit.setText(str(icon_dir))
            except Exception:
                pass
        dlg.icon_size_spin.setValue(int(s.value("ui/icon_size", 32)))
        theme = str(s.value("ui/theme", "light"))
        try:
            presets_map = { 'light':'Light', 'dark':'Dark', 'custom':'Custom' }
            dlg.preset_combo.setCurrentText(presets_map.get(theme, 'Light'))
            dlg._load_preset_values(dlg.preset_combo.currentText())
        except Exception:
            pass
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
            cust = getattr(win.view, '_custom_tools_overlay', None)
            if cust is not None:
                dlg.cust_x.setValue(cust.x())
                dlg.cust_y.setValue(cust.y())
                dlg.cust_w.setValue(cust.width())
                dlg.cust_h.setValue(cust.height())
        except Exception:
            pass

        # Menu builder defaults
        def getb(key: str, default: bool = True) -> bool:
            v = s.value(key)
            return default if v is None else (v in [True, 'true', '1'])
        dlg.cb_custom_visible.setChecked(getb("ui/menu/custom/visible", False))

        # Populate icon lists with order + visibility
        def get_order_and_vis(prefix: str, default_order: list[str]) -> tuple[list[str], dict[str, bool]]:
            order = s.value(f"ui/menu/{prefix}/order") or default_order
            if isinstance(order, str):
                order = [k for k in order.split(',') if k]
            vis: dict[str, bool] = {}
            for k in order:
                v = s.value(f"ui/menu/{prefix}/{k}")
                vis[k] = True if v is None else (v in [True,'true','1'])
            return order, vis
        main_default = ['save','load','scene_size','background','settings','reset_scene','reset_ui','toggle_library','toggle_inspector','toggle_timeline','toggle_custom']
        quick_default = ['zoom_out','zoom_in','fit','handles','onion']
        custom_default = ['save','load','scene_size','background','settings','zoom_out','zoom_in','fit','handles','onion']
        main_order, main_vis = get_order_and_vis('main', main_default)
        quick_order, quick_vis = get_order_and_vis('quick', quick_default)
        custom_order, custom_vis = get_order_and_vis('custom', custom_default)
        try:
            dlg.populate_icon_list(dlg.list_main_order, main_order, main_vis, dlg._main_specs)
            dlg.populate_icon_list(dlg.list_quick_order, quick_order, quick_vis, dlg._quick_specs)
            dlg.populate_icon_list(dlg.list_custom_order, custom_order, custom_vis, dlg._custom_specs)
        except Exception:
            pass

        # Onion values
        try:
            dlg.prev_count.setValue(int(s.value("onion/prev_count", 2)))
            dlg.next_count.setValue(int(s.value("onion/next_count", 1)))
            dlg.opacity_prev.setValue(float(s.value("onion/opacity_prev", 0.25)))
            dlg.opacity_next.setValue(float(s.value("onion/opacity_next", 0.18)))
        except Exception:
            pass

        if dlg.exec() == SettingsDialog.Accepted:
            # UI: icon directory and default overlay sizes
            icon_dir = dlg.icon_dir_edit.text().strip()
            s.setValue("ui/icon_dir", icon_dir if icon_dir else "")
            s.setValue("ui/icon_size", int(dlg.icon_size_spin.value()))
            theme = dlg.preset_combo.currentText().strip().lower() or 'light'
            s.setValue("ui/theme", theme)
            if theme == 'custom':
                try:
                    from ui.styles import build_stylesheet
                    css = build_stylesheet({
                        'bg_color': dlg.bg_edit.text() or '#E2E8F0',
                        'text_color': dlg.text_edit.text() or '#1A202C',
                        'accent_color': dlg.accent_edit.text() or '#E53E3E',
                        'hover_color': dlg.hover_edit.text() or '#E3E6FD',
                        'panel_bg': dlg.panel_edit.text() or '#F7F8FC',
                        'panel_opacity': (dlg.opacity_spin.value()/100.0),
                        'panel_border': dlg.border_edit.text() or '#D0D5DD',
                        'group_title_color': dlg.group_edit.text() or '#2D3748',
                        'radius': dlg.radius_spin.value(),
                        'font_size': dlg.font_spin.value(),
                    })
                    s.setValue('ui/custom_stylesheet', css)
                except Exception:
                    pass
            # Default sizes/positions
            s.setValue("ui/default/library_size", QSize(max(150, dlg.lib_w.value()), max(150, dlg.lib_h.value())))
            s.setValue("ui/default/inspector_size", QSize(max(150, dlg.insp_w.value()), max(150, dlg.insp_h.value())))
            s.setValue("ui/default/library_pos", QPoint(max(0, dlg.lib_x.value()), max(0, dlg.lib_y.value())))
            s.setValue("ui/default/inspector_pos", QPoint(max(0, dlg.insp_x.value()), max(0, dlg.insp_y.value())))
            s.setValue("ui/default/custom_pos", QPoint(max(0, dlg.cust_x.value()), max(0, dlg.cust_y.value())))
            s.setValue("ui/default/custom_size", QSize(max(100, dlg.cust_w.value()), max(60, dlg.cust_h.value())))
            # Apply immediate size/pos changes
            try:
                if dlg.lib_w.value() and dlg.lib_h.value():
                    win.library_overlay.resize(dlg.lib_w.value(), dlg.lib_h.value())
                if dlg.insp_w.value() and dlg.insp_h.value():
                    win.inspector_overlay.resize(dlg.insp_w.value(), dlg.insp_h.value())
                win.library_overlay.move(max(0, dlg.lib_x.value()), max(0, dlg.lib_y.value()))
                win.inspector_overlay.move(max(0, dlg.insp_x.value()), max(0, dlg.insp_y.value()))
                cust = getattr(win.view, '_custom_tools_overlay', None)
                if cust is not None:
                    cust.resize(max(100, dlg.cust_w.value()), max(60, dlg.cust_h.value()))
                    cust.move(max(0, dlg.cust_x.value()), max(0, dlg.cust_y.value()))
            except Exception:
                pass

            # Custom overlay visibility
            s.setValue("ui/menu/custom/visible", dlg.cb_custom_visible.isChecked())

            # Orders and visibility
            main_order, main_vis = dlg.extract_icon_list(dlg.list_main_order)
            quick_order, quick_vis = dlg.extract_icon_list(dlg.list_quick_order)
            custom_order, custom_vis = dlg.extract_icon_list(dlg.list_custom_order)
            s.setValue("ui/menu/main/order", main_order)
            s.setValue("ui/menu/quick/order", quick_order)
            s.setValue("ui/menu/custom/order", custom_order)
            for k, v in main_vis.items(): s.setValue(f"ui/menu/main/{k}", v)
            for k, v in quick_vis.items(): s.setValue(f"ui/menu/quick/{k}", v)
            for k, v in custom_vis.items(): s.setValue(f"ui/menu/custom/{k}", v)

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
            except Exception:
                pass

            # Refresh icons everywhere
            try:
                import ui.icons as app_icons
                app_icons.clear_cache()
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
                except Exception:
                    pass
                win.set_custom_overlay_visible(bool(s.value("ui/menu/custom/visible") in [True,'true','1']))
            except Exception:
                pass

            # Apply theme immediately
            try:
                apply_stylesheet(QApplication.instance())
            except Exception:
                pass
