"""Main window of the application, orchestrating UI components and scene management."""

import logging
from typing import Any, Dict

from PySide6.QtCore import Qt, QTimer, QEvent, QSettings
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QMainWindow,
    QGraphicsScene,
    QVBoxLayout,
    QWidget,
    QFrame,
    QMessageBox,
)

from ui.scene import scene_io, actions as scene_actions
from core.scene_model import SceneModel, Keyframe
from ui import actions as app_actions
from ui import selection_sync
from ui.object_manager import ObjectManager
from ui.onion_skin import OnionSkinManager
from ui.overlay_manager import OverlayManager
from ui.playback_controller import PlaybackController
from ui.scene.scene_controller import SceneController
from ui.scene.scene_visuals import SceneVisuals
from ui.settings_manager import SettingsManager
from ui.timeline_widget import TimelineWidget
from ui.docks import setup_timeline_dock
from ui.zoomable_view import ZoomableView
from ui.library import actions as library_actions
from ui.inspector import actions as inspector_actions


class MainWindow(QMainWindow):
    """Main application window.

    This class orchestrates all UI components, including the scene, timeline,
    inspector, and library. It holds the central `SceneModel` and manages
    interactions between different parts of the UI.
    """

    def __init__(self) -> None:
        """Initializes the main window, scene, and all UI components."""
        super().__init__()
        self.setWindowTitle("Borne and the Bayrou - Disco MIX")

        # Core components (model, scene, object manager) must exist before
        # any other setup step.  They are grouped into a dedicated function so
        # tests can rely on their availability.
        self.setup_core_components()

        # Ordered list of setup hooks documenting the startup sequence.
        self._setup_hooks = [
            self._setup_scene,
            self._setup_overlays,
            lambda: setattr(self, "timeline_widget", setup_timeline_dock(self)),
            self._setup_playback,
            self._setup_actions,
            self._setup_tool_overlays,
            self._setup_scene_visuals,
            self._setup_scene_controller,
        ]
        for hook in self._setup_hooks:
            hook()

        self._connect_actions()
        self._startup_sequence()
        self._setup_settings()
        self._apply_startup_preferences()

    # --- Core setup -----------------------------------------------------
    def setup_core_components(self) -> None:
        """Create the scene model, Qt scene and object manager."""
        self.scene_model: SceneModel = SceneModel()
        self.scene: QGraphicsScene = QGraphicsScene()
        self.scene.setSceneRect(
            0, 0, self.scene_model.scene_width, self.scene_model.scene_height
        )
        self.object_manager: ObjectManager = ObjectManager(self)

    def _setup_scene(self) -> None:
        """Initializes the view and related state."""
        self.zoom_factor: float = 1.0
        self._suspend_item_updates: bool = False
        self._settings_loaded: bool = False

        self.view: ZoomableView = ZoomableView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setFrameShape(QFrame.NoFrame)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        main_widget: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view)
        self.setCentralWidget(main_widget)

    def _setup_overlays(self) -> None:
        """Initializes overlay and onion skin managers."""
        self.overlays = OverlayManager(self)
        self.overlays.build_overlays()
        self.onion: OnionSkinManager = OnionSkinManager(self)

    def _setup_playback(self) -> None:
        """Initializes the playback controller."""
        self.playback_handler: PlaybackController = PlaybackController(
            self.scene_model, self.timeline_widget, self.inspector_widget, self
        )

    def _setup_actions(self) -> None:
        """Builds application actions."""
        app_actions.build_actions(self)

    def _setup_tool_overlays(self) -> None:
        """Builds tool overlays for the view."""
        self.view._build_main_tools_overlay(self)
        try:
            self.view._build_custom_tools_overlay(self)
        except RuntimeError as e:
            logging.debug("Custom overlay not built: %s", e)

    def _setup_scene_controller(self) -> None:
        """Creates the scene controller facade."""
        self.scene_controller: SceneController = SceneController(
            self, visuals=self.visuals, onion=self.onion
        )

    def _connect_actions(self) -> None:
        """Connects application actions to their slots."""
        app_actions.connect_signals(self)

    def _startup_sequence(self) -> None:
        """Runs the UI startup sequence."""
        self.showMaximized()
        self.timeline_dock.show()
        self.timeline_dock.visibilityChanged.connect(lambda _: self.ensure_fit())
        self.timeline_dock.topLevelChanged.connect(lambda _: self.ensure_fit())
        self.ensure_fit()
        scene_io.create_blank_scene(self)
        self.ensure_fit()
        self.scene.selectionChanged.connect(self._on_scene_selection_changed)

    def _setup_settings(self) -> None:
        """Initializes the settings manager and loads settings."""
        self.settings = SettingsManager(self)
        self.load_settings()

    def _apply_startup_preferences(self) -> None:
        """Applies stored startup preferences."""
        try:
            s = QSettings("JaJa", "Macronotron")
            self.onion.prev_count = int(s.value("onion/prev_count", self.onion.prev_count))
            self.onion.next_count = int(s.value("onion/next_count", self.onion.next_count))
            self.onion.opacity_prev = float(s.value("onion/opacity_prev", self.onion.opacity_prev))
            self.onion.opacity_next = float(s.value("onion/opacity_next", self.onion.opacity_next))
            self.overlays.apply_menu_settings()
        except (RuntimeError, ValueError, ImportError):
            logging.exception("Failed to apply startup preferences")

    def showEvent(self, event: QEvent) -> None:
        """Ensures the view is fitted and overlays are positioned on show."""
        super().showEvent(event)
        def _layout_then_fit():
            try:
                self.resizeDocks([self.timeline_dock], [int(max(140, self.height()*0.22))], Qt.Vertical)
            except RuntimeError as e:
                logging.debug("Failed to resize docks: %s", e)
            self.fit_to_view()
            self._position_overlays()
        QTimer.singleShot(0, _layout_then_fit)
        QTimer.singleShot(200, self._position_overlays)

    def _position_overlays(self) -> None:
        """Positions the overlays in the main window."""
        self.overlays.position_overlays()

    def reset_ui(self) -> None:
        """Clears saved UI settings and resets the UI to its default state immediately."""
        self.settings.clear()

        self.showMaximized()
        self._settings_loaded = False
        self._position_overlays()

        QMessageBox.information(self, "Interface réinitialisée", "La disposition de l'interface a été réinitialisée.")

    def reset_scene(self) -> None:
        """Resets the scene to a blank state."""
        scene_actions.reset_scene(self)

    def _build_side_overlays(self) -> None:
        """Builds the side overlays for the library and inspector."""
        # Compat shim: use OverlayManager now
        self.overlays.build_overlays()

    def set_library_overlay_visible(self, visible: bool) -> None:
        """Sets the visibility of the library overlay."""
        library_actions.set_library_overlay_visible(self, visible)

    def set_inspector_overlay_visible(self, visible: bool) -> None:
        """Sets the visibility of the inspector overlay."""
        inspector_actions.set_inspector_overlay_visible(self, visible)

    def set_custom_overlay_visible(self, visible: bool) -> None:
        """Sets the visibility of the custom overlay."""
        self.overlays.set_custom_visible(visible)

    def _setup_scene_visuals(self) -> None:
        """Sets up the scene visuals."""
        self.visuals = SceneVisuals(self)
        self.visuals.setup()

    def _update_scene_visuals(self) -> None:
        """Updates the scene visuals."""
        self.scene_controller.update_scene_visuals()

    def _update_zoom_status(self) -> None:
        """Updates the zoom status."""
        # No status bar or zoom label; keep overlay minimal
        pass

    def fit_to_view(self) -> None:
        """Fits the scene to the view."""
        self.view.resetTransform()
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.zoom_factor = self.view.transform().m11()
        self._update_zoom_status()

    def ensure_fit(self) -> None:
        """Ensures the scene is fitted to the view."""
        QTimer.singleShot(0, self.fit_to_view)

    def set_scene_size(self) -> None:
        """Sets the scene size."""
        scene_actions.set_scene_size(self)

    def set_background(self) -> None:
        """Sets the background of the scene."""
        scene_actions.set_background(self)

    def _update_background(self):
        """Updates the background of the scene."""
        # Délégation via SceneController (comportement inchangé)
        self.scene_controller.update_background()

    def toggle_rotation_handles(self, visible: bool) -> None:
        """Toggles the visibility of the rotation handles."""
        self.scene_controller.set_rotation_handles_visible(visible)

    def update_scene_from_model(self) -> None:
        """Updates the scene from the model."""
        index: int = self.scene_model.current_frame
        keyframes: Dict[int, Keyframe] = self.scene_model.keyframes
        if not keyframes:
            return

        graphics_items: Dict[str, Any] = self.object_manager.graphics_items
        logging.debug(f"update_scene_from_model: frame={index}, keyframes={list(keyframes.keys())}")

        self._apply_puppet_states(graphics_items, keyframes, index)
        self._apply_object_states(graphics_items, keyframes, index)

    def _apply_puppet_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Keyframe], index: int) -> None:
        """Applies the puppet states to the scene."""
        self.scene_controller.apply_puppet_states(graphics_items, keyframes, index)

    def _apply_object_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Keyframe], index: int) -> None:
        """Applies the object states to the scene."""
        self.scene_controller.apply_object_states(graphics_items, keyframes, index)

    def add_keyframe(self, frame_index: int) -> None:
        """Adds a keyframe to the scene."""
        state = self.object_manager.capture_scene_state()
        self.scene_model.add_keyframe(frame_index, state)
        self.timeline_widget.add_keyframe_marker(frame_index)

    def select_object_in_inspector(self, name: str) -> None:
        """Selects an object in the inspector."""
        selection_sync.select_object_in_inspector(self, name)

    def _on_scene_selection_changed(self) -> None:
        """Handles the scene selection changed event."""
        selection_sync.scene_selection_changed(self)
    def _on_frame_update(self) -> None:
        """Handles the frame update event."""
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
        """Enables or disables onion skinning."""
        # Délégation via SceneController
        self.scene_controller.set_onion_enabled(enabled)

    def clear_onion_skins(self) -> None:
        """Clears the onion skins."""
        self.scene_controller.clear_onion_skins()

    def update_onion_skins(self) -> None:
        """Updates the onion skins."""
        self.scene_controller.update_onion_skins()

    # --- Settings Dialog ---
    def open_settings_dialog(self) -> None:
        """Opens the settings dialog."""
        # Délègue entièrement au SettingsManager
        self.settings.open_dialog()
