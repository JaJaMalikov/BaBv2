import logging
from typing import Optional, Any, Dict

from PySide6.QtWidgets import (
    QMainWindow,
    QGraphicsScene,
    QVBoxLayout,
    QWidget,
    QDockWidget,
    QFrame,
    QMessageBox,
)
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QTimer, QEvent

from core.scene_model import SceneModel, Keyframe
from core.puppet_piece import PuppetPiece
from ui.timeline_widget import TimelineWidget
from ui.zoomable_view import ZoomableView
from ui.playback_handler import PlaybackHandler
from ui.object_manager import ObjectManager
from ui.onion_skin import OnionSkinManager
from ui.panels import build_side_overlays
from ui.scene_visuals import SceneVisuals
from ui import actions as app_actions
from ui.settings_manager import SettingsManager
from ui.state_applier import StateApplier
from ui import selection_sync
from ui import scene_settings
from ui import scene_commands
from ui.settings_dialog import SettingsDialog
from PySide6.QtCore import QSettings, QSize

import ui.scene_io as scene_io


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Borne and the Bayrou - Disco MIX")

        self.scene_model: SceneModel = SceneModel()
        self.zoom_factor: float = 1.0
        self._suspend_item_updates: bool = False
        self._settings_loaded: bool = False

        self.scene: QGraphicsScene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.scene_model.scene_width, self.scene_model.scene_height)

        self.object_manager: ObjectManager = ObjectManager(self)

        self.view: ZoomableView = ZoomableView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setFrameShape(QFrame.NoFrame)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Build large overlays (library, inspector) before actions so toggles can bind
        self._build_side_overlays()

        # Onion skin manager
        self.onion: OnionSkinManager = OnionSkinManager(self)

        main_widget: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view)
        self.setCentralWidget(main_widget)

        self.timeline_dock: QDockWidget = QDockWidget("", self)
        self.timeline_dock.setObjectName("dock_timeline")
        self.timeline_widget: TimelineWidget = TimelineWidget()
        self.timeline_dock.setWidget(self.timeline_widget)
        self.timeline_dock.setFeatures(QDockWidget.DockWidgetClosable)
        try:
            from PySide6.QtWidgets import QWidget as _QW
            self.timeline_dock.setTitleBarWidget(_QW())
        except Exception as e:
            logging.debug("Custom title bar not set on dock: %s", e)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.timeline_dock)

        # Inspector and Library now live as overlays (see _build_side_overlays)

        self.playback_handler: PlaybackHandler = PlaybackHandler(self.scene_model, self.timeline_widget, self.inspector_widget, self)

        app_actions.build_actions(self)
        self.view._build_main_tools_overlay(self)
        # Build optional custom overlay
        try:
            self.view._build_custom_tools_overlay(self)
        except Exception as e:
            logging.debug("Custom overlay not built: %s", e)
        app_actions.connect_signals(self)
        self._setup_scene_visuals()

        # --- Startup Sequence ---
        self.showMaximized()
        self.timeline_dock.show()
        self.timeline_dock.visibilityChanged.connect(lambda _: self.ensure_fit())
        self.timeline_dock.topLevelChanged.connect(lambda _: self.ensure_fit())
        self.ensure_fit()
        scene_io.create_blank_scene(self, add_default_puppet=False)
        self.ensure_fit()
        self.scene.selectionChanged.connect(self._on_scene_selection_changed)

        # Settings manager
        self.settings = SettingsManager(self)
        self.load_settings()
        # State applier
        self.state_applier = StateApplier(self)
        # Apply startup preferences (onion, overlays menu)
        try:
            from PySide6.QtCore import QSettings
            s = QSettings("JaJa", "Macronotron")
            # Onion
            self.onion.prev_count = int(s.value("onion/prev_count", self.onion.prev_count))
            self.onion.next_count = int(s.value("onion/next_count", self.onion.next_count))
            self.onion.opacity_prev = float(s.value("onion/opacity_prev", self.onion.opacity_prev))
            self.onion.opacity_next = float(s.value("onion/opacity_next", self.onion.opacity_next))
            # Overlays menu settings applied during build via view methods
            self.view.apply_menu_settings_main()
            self.view.apply_menu_settings_quick()
        except Exception:
            pass

    def showEvent(self, event: QEvent) -> None:
        super().showEvent(event)
        def _layout_then_fit():
            try:
                self.resizeDocks([self.timeline_dock], [int(max(140, self.height()*0.22))], Qt.Vertical)
            except Exception as e:
                logging.debug("Failed to resize docks: %s", e)
            self.fit_to_view()
            self._position_overlays()
        QTimer.singleShot(0, _layout_then_fit)
        QTimer.singleShot(200, self._position_overlays)

    def _position_overlays(self) -> None:
        from ui.panels import position_overlays
        position_overlays(self)

    def reset_ui(self) -> None:
        """Clears saved UI settings and resets the UI to its default state immediately."""
        self.settings.clear()

        self.showMaximized()
        self._settings_loaded = False
        self._position_overlays()

        QMessageBox.information(self, "Interface réinitialisée", "La disposition de l'interface a été réinitialisée.") 

    def reset_scene(self) -> None:
        scene_commands.reset_scene(self)

    def _build_side_overlays(self) -> None:
        self.library_overlay, self.library_widget, self.inspector_overlay, self.inspector_widget = build_side_overlays(self)

    def set_library_overlay_visible(self, visible: bool) -> None:
        self.library_overlay.setVisible(visible)
        self.toggle_library_action.blockSignals(True)
        self.toggle_library_action.setChecked(visible)
        self.toggle_library_action.blockSignals(False)

    def set_inspector_overlay_visible(self, visible: bool) -> None:
        self.inspector_overlay.setVisible(visible)
        self.toggle_inspector_action.blockSignals(True)
        self.toggle_inspector_action.setChecked(visible)
        self.toggle_inspector_action.blockSignals(False)

    def set_custom_overlay_visible(self, visible: bool) -> None:
        overlay = getattr(self.view, '_custom_tools_overlay', None)
        if overlay is not None:
            overlay.setVisible(visible)
        self.toggle_custom_action.blockSignals(True)
        self.toggle_custom_action.setChecked(visible)
        self.toggle_custom_action.blockSignals(False)

    def _setup_scene_visuals(self) -> None:
        self.visuals = SceneVisuals(self)
        self.visuals.setup()

    def _update_scene_visuals(self) -> None:
        self.visuals.update_scene_visuals()

    def _update_zoom_status(self) -> None:
        # No status bar or zoom label; keep overlay minimal
        pass

    def zoom(self, factor: float) -> None:
        self.view.scale(factor, factor)
        self.zoom_factor *= factor
        self._update_zoom_status()

    def fit_to_view(self) -> None:
        self.view.resetTransform()
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.zoom_factor = self.view.transform().m11()
        self._update_zoom_status()

    def ensure_fit(self) -> None:
        QTimer.singleShot(0, self.fit_to_view)

    def set_scene_size(self) -> None:
        scene_settings.set_scene_size(self)

    def set_background(self) -> None:
        scene_commands.set_background(self)

    def _update_background(self):
        self.visuals.update_background()

    def toggle_rotation_handles(self, visible: bool) -> None:
        for item in self.object_manager.graphics_items.values():
            if isinstance(item, PuppetPiece):
                item.set_handle_visibility(visible)
        self.view.handles_btn.setChecked(visible)

    def update_scene_from_model(self) -> None:
        index: int = self.scene_model.current_frame
        keyframes: Dict[int, Keyframe] = self.scene_model.keyframes
        if not keyframes:
            return

        graphics_items: Dict[str, Any] = self.object_manager.graphics_items
        logging.debug(f"update_scene_from_model: frame={index}, keyframes={list(keyframes.keys())}")

        self._apply_puppet_states(graphics_items, keyframes, index)
        self._apply_object_states(graphics_items, keyframes, index)

    def _apply_puppet_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Keyframe], index: int) -> None:
        self.state_applier.apply_puppet_states(graphics_items, keyframes, index)

    def _apply_object_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Keyframe], index: int) -> None:
        self.state_applier.apply_object_states(graphics_items, keyframes, index)

    def add_keyframe(self, frame_index: int) -> None:
        puppet_states: Dict[str, Dict[str, Dict[str, Any]]] = self.object_manager.capture_puppet_states()
        self.scene_model.add_keyframe(frame_index, puppet_states)
        # Overwrite objects with the on-screen capture so we don't serialize stale/global attachment
        kf: Optional[Keyframe] = self.scene_model.keyframes.get(frame_index)
        if kf is not None:
            kf.objects = self.object_manager.capture_visible_object_states()
        self.timeline_widget.add_keyframe_marker(frame_index)

    def select_object_in_inspector(self, name: str) -> None:
        selection_sync.select_object_in_inspector(self, name)

    def _on_scene_selection_changed(self) -> None:
        selection_sync.scene_selection_changed(self)
    def _on_frame_update(self) -> None:
        self.update_scene_from_model()
        self.update_onion_skins()

    def closeEvent(self, event: QEvent) -> None:
        """Save settings when the window is closed."""
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self) -> None:
        """Save window and panel geometries to QSettings."""
        self.settings.save()

    def load_settings(self) -> None:
        """Load and apply window and panel geometries from QSettings."""
        self.settings.load()

    def set_onion_enabled(self, enabled: bool) -> None:
        self.onion.set_enabled(enabled)

    def clear_onion_skins(self) -> None:
        self.onion.clear()

    def update_onion_skins(self) -> None:
        self.onion.update()

    # --- Settings Dialog ---
    def open_settings_dialog(self) -> None:
        dlg = SettingsDialog(self)
        # Prefill UI values only
        # Prefill UI section
        s = QSettings("JaJa", "Macronotron")
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
        # Default sizes from settings or current
        try:
            dlg.lib_w.setValue(self.library_overlay.width())
            dlg.lib_h.setValue(self.library_overlay.height())
            dlg.insp_w.setValue(self.inspector_overlay.width())
            dlg.insp_h.setValue(self.inspector_overlay.height())
            # Positions
            dlg.lib_x.setValue(self.library_overlay.x())
            dlg.lib_y.setValue(self.library_overlay.y())
            dlg.insp_x.setValue(self.inspector_overlay.x())
            dlg.insp_y.setValue(self.inspector_overlay.y())
            cust = getattr(self.view, '_custom_tools_overlay', None)
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

        # Populate icon lists with order + visibility and matching icons
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
            s = QSettings("JaJa", "Macronotron")
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
            # Default sizes
            s.setValue("ui/default/library_size", QSize(max(150, dlg.lib_w.value()), max(150, dlg.lib_h.value())))
            s.setValue("ui/default/inspector_size", QSize(max(150, dlg.insp_w.value()), max(150, dlg.insp_h.value())))
            # Default positions
            from PySide6.QtCore import QPoint
            s.setValue("ui/default/library_pos", QPoint(max(0, dlg.lib_x.value()), max(0, dlg.lib_y.value())))
            s.setValue("ui/default/inspector_pos", QPoint(max(0, dlg.insp_x.value()), max(0, dlg.insp_y.value())))
            s.setValue("ui/default/custom_pos", QPoint(max(0, dlg.cust_x.value()), max(0, dlg.cust_y.value())))
            s.setValue("ui/default/custom_size", QSize(max(100, dlg.cust_w.value()), max(60, dlg.cust_h.value())))
            # Apply immediate size change if values given
            lib_w, lib_h = dlg.lib_w.value(), dlg.lib_h.value()
            insp_w, insp_h = dlg.insp_w.value(), dlg.insp_h.value()
            # Resize overlays now to match new defaults
            try:
                if lib_w and lib_h:
                    self.library_overlay.resize(lib_w, lib_h)
                if insp_w and insp_h:
                    self.inspector_overlay.resize(insp_w, insp_h)
                # Move overlays now to chosen defaults
                self.library_overlay.move(max(0, dlg.lib_x.value()), max(0, dlg.lib_y.value()))
                self.inspector_overlay.move(max(0, dlg.insp_x.value()), max(0, dlg.insp_y.value()))
                cust = getattr(self.view, '_custom_tools_overlay', None)
                if cust is not None:
                    cust.resize(max(100, dlg.cust_w.value()), max(60, dlg.cust_h.value()))
                    cust.move(max(0, dlg.cust_x.value()), max(0, dlg.cust_y.value()))
            except Exception:
                pass

            # Custom overlay visibility toggle remains
            s.setValue("ui/menu/custom/visible", dlg.cb_custom_visible.isChecked())

            # Store orders and visibility from icon lists
            main_order, main_vis = dlg.extract_icon_list(dlg.list_main_order)
            quick_order, quick_vis = dlg.extract_icon_list(dlg.list_quick_order)
            custom_order, custom_vis = dlg.extract_icon_list(dlg.list_custom_order)
            s.setValue("ui/menu/main/order", main_order)
            s.setValue("ui/menu/quick/order", quick_order)
            s.setValue("ui/menu/custom/order", custom_order)
            for k, v in main_vis.items(): s.setValue(f"ui/menu/main/{k}", v)
            for k, v in quick_vis.items(): s.setValue(f"ui/menu/quick/{k}", v)
            for k, v in custom_vis.items(): s.setValue(f"ui/menu/custom/{k}", v)

            # Store onion settings
            s.setValue("onion/prev_count", int(dlg.prev_count.value()))
            s.setValue("onion/next_count", int(dlg.next_count.value()))
            s.setValue("onion/opacity_prev", float(dlg.opacity_prev.value()))
            s.setValue("onion/opacity_next", float(dlg.opacity_next.value()))

            # Refresh icons if icon directory changed
            try:
                import ui.icons as app_icons
                app_icons.clear_cache()
                # Update action icons
                from ui.icons import (
                    icon_scene_size, icon_background, icon_library, icon_inspector, icon_timeline,
                    icon_save, icon_open, icon_reset_ui, icon_reset_scene
                )
                self.save_action.setIcon(icon_save())
                self.load_action.setIcon(icon_open())
                self.scene_size_action.setIcon(icon_scene_size())
                self.background_action.setIcon(icon_background())
                self.reset_scene_action.setIcon(icon_reset_scene())
                self.reset_ui_action.setIcon(icon_reset_ui())
                self.toggle_library_action.setIcon(icon_library())
                self.toggle_inspector_action.setIcon(icon_inspector())
                self.timeline_dock.toggleViewAction().setIcon(icon_timeline())
                # Update overlay buttons
                self.view.refresh_overlay_icons(self)
                # Re-apply menu settings for overlays
                self.view.apply_menu_settings_main()
                self.view.apply_menu_settings_quick()
                # Rebuild custom overlay visibility/order
                try:
                    self.view._build_custom_tools_overlay(self)
                except Exception:
                    pass
                self.set_custom_overlay_visible(bool(s.value("ui/menu/custom/visible") in [True,'true','1']))
            except Exception:
                pass

            # Apply theme immediately
            try:
                from ui.styles import apply_stylesheet
                from PySide6.QtWidgets import QApplication
                apply_stylesheet(QApplication.instance())
            except Exception:
                pass
            # Apply onion advanced
            try:
                self.onion.prev_count = int(dlg.prev_count.value())
                self.onion.next_count = int(dlg.next_count.value())
                self.onion.opacity_prev = float(dlg.opacity_prev.value())
                self.onion.opacity_next = float(dlg.opacity_next.value())
                self.update_onion_skins()
            except Exception:
                pass
