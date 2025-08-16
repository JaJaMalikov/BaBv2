"""Module for creating and connecting QActions in the main window."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtCore import QSettings

from ui.scene import scene_io
from ui.scene import actions as scene_actions
from ui.library import actions as library_actions
from ui.inspector import actions as inspector_actions
from ui.icons import (
    icon_scene_size, icon_background, icon_library, icon_inspector, icon_timeline,
    icon_save, icon_open, icon_reset_ui, icon_reset_scene, get_icon
)


def build_actions(win: Any) -> None:
    """Create and attach QActions to the given MainWindow instance.

    Exposes attributes on win: save_action, load_action, scene_size_action, background_action,
    reset_scene_action, reset_ui_action, toggle_library_action, toggle_inspector_action.
    Also decorates the timeline dock toggle action with an icon.
    """
    win.save_action = QAction(icon_save(), "Sauvegarder", win)
    win.save_action.setShortcut("Ctrl+S")
    win.load_action = QAction(icon_open(), "Charger", win)
    win.load_action.setShortcut("Ctrl+O")
    win.scene_size_action = QAction(icon_scene_size(), "Taille Scène", win)
    win.background_action = QAction(icon_background(), "Image de fond", win)
    # Use 'layers' icon as settings indicator
    win.settings_action = QAction(get_icon('layers'), "Paramètres", win)

    win.reset_scene_action = QAction(icon_reset_scene(), "Réinitialiser la scène", win)
    win.reset_ui_action = QAction(icon_reset_ui(), "Réinitialiser l'interface", win)

    # Overlay toggles
    win.toggle_library_action = QAction(icon_library(), "Bibliothèque", win)
    win.toggle_library_action.setCheckable(True)
    win.toggle_library_action.setChecked(win.library_overlay.isVisible())
    win.toggle_library_action.toggled.connect(lambda v: library_actions.set_library_overlay_visible(win, v))

    win.toggle_inspector_action = QAction(icon_inspector(), "Inspecteur", win)
    win.toggle_inspector_action.setCheckable(True)
    win.toggle_inspector_action.setChecked(win.inspector_overlay.isVisible())
    win.toggle_inspector_action.toggled.connect(lambda v: inspector_actions.set_inspector_overlay_visible(win, v))

    # Timeline toggle (dock)
    win.timeline_dock.toggleViewAction().setIcon(icon_timeline())

    # Custom overlay toggle
    win.toggle_custom_action = QAction(get_icon('layers'), "Custom", win)
    win.toggle_custom_action.setCheckable(True)

    # Map action keys for shortcut management
    win.shortcuts = {
        "save": win.save_action,
        "load": win.load_action,
        "scene_size": win.scene_size_action,
        "background": win.background_action,
        "settings": win.settings_action,
        "reset_scene": win.reset_scene_action,
        "reset_ui": win.reset_ui_action,
        "toggle_library": win.toggle_library_action,
        "toggle_inspector": win.toggle_inspector_action,
        "toggle_custom": win.toggle_custom_action,
    }

    # Load persisted shortcuts
    s = QSettings("JaJa", "Macronotron")
    s.beginGroup("shortcuts")
    for key, action in win.shortcuts.items():
        seq = s.value(key)
        if seq:
            action.setShortcut(seq)
    s.endGroup()


def connect_signals(win: Any) -> None:
    """Wire UI actions and component signals to MainWindow slots."""
    # Scene I/O
    win.save_action.triggered.connect(lambda: scene_io.save_scene(win))
    win.load_action.triggered.connect(lambda: scene_io.load_scene(win))
    win.reset_scene_action.triggered.connect(lambda: scene_actions.reset_scene(win))
    win.reset_ui_action.triggered.connect(win.reset_ui)
    win.settings_action.triggered.connect(win.open_settings_dialog)

    # Scene settings
    win.scene_size_action.triggered.connect(lambda: scene_actions.set_scene_size(win))
    win.background_action.triggered.connect(lambda: scene_actions.set_background(win))

    # ZoomableView signals
    win.view.zoom_requested.connect(win.scene_controller.zoom)
    win.view.fit_requested.connect(win.fit_to_view)
    win.view.handles_toggled.connect(win.toggle_rotation_handles)
    win.view.onion_toggled.connect(win.set_onion_enabled)
    win.view.item_dropped.connect(win.scene_controller.handle_library_drop)
    win.toggle_custom_action.toggled.connect(win.set_custom_overlay_visible)

    # PlaybackHandler signals
    win.playback_handler.snapshot_requested.connect(win.object_manager.snapshot_current_frame)
    win.playback_handler.frame_update_requested.connect(win._on_frame_update)
    win.playback_handler.keyframe_add_requested.connect(win.add_keyframe)

    # Library signals
    win.library_widget.addRequested.connect(win.scene_controller._add_library_item_to_scene)
