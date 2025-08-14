import logging
from typing import Optional, Any, Dict

from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QMainWindow,
    QGraphicsScene,
    QVBoxLayout,
    QWidget,
    QDockWidget,
    QFrame,
    QMessageBox,
)

import ui.scene_io as scene_io
from core.scene_model import SceneModel, Keyframe
from ui import actions as app_actions
from ui import scene_commands
from ui import scene_settings
from ui import selection_sync
from ui.object_manager import ObjectManager
from ui.onion_skin import OnionSkinManager
from ui.overlay_manager import OverlayManager
from ui.playback_controller import PlaybackController
from ui.scene_controller import SceneController
from ui.scene_visuals import SceneVisuals
from ui.settings_manager import SettingsManager
from ui.timeline_widget import TimelineWidget
from ui.zoomable_view import ZoomableView


class MainWindow(QMainWindow):
    """
    """
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
        self.overlays = OverlayManager(self)
        self.overlays.build_overlays()

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

        self.playback_handler: PlaybackController = PlaybackController(self.scene_model, self.timeline_widget, self.inspector_widget, self)

        app_actions.build_actions(self)
        self.view._build_main_tools_overlay(self)
        # Build optional custom overlay
        try:
            self.view._build_custom_tools_overlay(self)
        except Exception as e:
            logging.debug("Custom overlay not built: %s", e)
        self._setup_scene_visuals()
        # Scene controller façade (agrège visuals, onion, applier)
        self.scene_controller: SceneController = SceneController(self, visuals=self.visuals, onion=self.onion)
        app_actions.connect_signals(self)
        # --- Startup Sequence ---
        self.showMaximized()
        self.timeline_dock.show()
        self.timeline_dock.visibilityChanged.connect(lambda _: self.ensure_fit())
        self.timeline_dock.topLevelChanged.connect(lambda _: self.ensure_fit())
        self.ensure_fit()
        scene_io.create_blank_scene(self)
        self.ensure_fit()
        self.scene.selectionChanged.connect(self._on_scene_selection_changed)

        # Settings manager
        self.settings = SettingsManager(self)
        self.load_settings()
        # State applier désormais exposé via SceneController
        # Apply startup preferences (onion, overlays menu)
        try:
            from PySide6.QtCore import QSettings
            s = QSettings("JaJa", "Macronotron")
            # Onion
            self.onion.prev_count = int(s.value("onion/prev_count", self.onion.prev_count))
            self.onion.next_count = int(s.value("onion/next_count", self.onion.next_count))
            self.onion.opacity_prev = float(s.value("onion/opacity_prev", self.onion.opacity_prev))
            self.onion.opacity_next = float(s.value("onion/opacity_next", self.onion.opacity_next))
            # Overlays menu settings applied during build via manager
            self.overlays.apply_menu_settings()
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
        self.overlays.position_overlays()

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
        # Compat shim: use OverlayManager now
        self.overlays.build_overlays()

    def set_library_overlay_visible(self, visible: bool) -> None:
        self.overlays.set_library_visible(visible)

    def set_inspector_overlay_visible(self, visible: bool) -> None:
        self.overlays.set_inspector_visible(visible)

    def set_custom_overlay_visible(self, visible: bool) -> None:
        self.overlays.set_custom_visible(visible)

    def _setup_scene_visuals(self) -> None:
        self.visuals = SceneVisuals(self)
        self.visuals.setup()

    def _update_scene_visuals(self) -> None:
        self.scene_controller.update_scene_visuals()

    def _update_zoom_status(self) -> None:
        # No status bar or zoom label; keep overlay minimal
        pass

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
        # Délégation via SceneController (comportement inchangé)
        self.scene_controller.update_background()

    def toggle_rotation_handles(self, visible: bool) -> None:
        self.scene_controller.set_rotation_handles_visible(visible)

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
        self.scene_controller.apply_puppet_states(graphics_items, keyframes, index)

    def _apply_object_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Keyframe], index: int) -> None:
        self.scene_controller.apply_object_states(graphics_items, keyframes, index)

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
        # Délégation via SceneController
        self.scene_controller.set_onion_enabled(enabled)

    def clear_onion_skins(self) -> None:
        self.scene_controller.clear_onion_skins()

    def update_onion_skins(self) -> None:
        self.scene_controller.update_onion_skins()

    # --- Settings Dialog ---
    def open_settings_dialog(self) -> None:
        # Délègue entièrement au SettingsManager
        self.settings.open_dialog()
