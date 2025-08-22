"""Module for creating and connecting QActions in the main window."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction, QKeySequence

from ui.icons import (
    get_icon,
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
from ui.views.inspector import actions as inspector_actions
from ui.views.library import actions as library_actions
from ui.scene import actions as scene_actions
from ui.scene import scene_io

logger = logging.getLogger(__name__)


def build_actions(win: Any) -> None:
    """
    Create and attach QActions to the given MainWindow instance.

    This function creates all the actions for the main window and sets their
    properties like icons and shortcuts. It also exposes the actions as attributes
    of the main window instance.

    Args:
        win: The MainWindow instance.
    """
    win.save_action = QAction(icon_save(), "Sauvegarder", win)
    win.save_action.setShortcut("Ctrl+S")
    win.load_action = QAction(icon_open(), "Charger", win)
    win.load_action.setShortcut("Ctrl+O")
    win.scene_size_action = QAction(icon_scene_size(), "Taille Scène", win)
    win.background_action = QAction(icon_background(), "Image de fond", win)
    win.add_light_action = QAction(get_icon("plus"), "Ajouter Projecteur", win)
    # Settings icon: configurable via key 'settings'
    win.settings_action = QAction(get_icon("settings"), "Paramètres", win)

    win.reset_scene_action = QAction(icon_reset_scene(), "Réinitialiser la scène", win)
    win.reset_ui_action = QAction(icon_reset_ui(), "Réinitialiser l'interface", win)

    # Overlay toggles
    win.toggle_library_action = QAction(icon_library(), "Bibliothèque", win)
    win.toggle_library_action.setCheckable(True)
    win.toggle_library_action.setChecked(win.library_overlay.isVisible())
    win.toggle_library_action.toggled.connect(
        lambda v: library_actions.set_library_overlay_visible(win, v)
    )

    win.toggle_inspector_action = QAction(icon_inspector(), "Inspecteur", win)
    win.toggle_inspector_action.setCheckable(True)
    win.toggle_inspector_action.setChecked(win.inspector_overlay.isVisible())
    win.toggle_inspector_action.toggled.connect(
        lambda v: inspector_actions.set_inspector_overlay_visible(win, v)
    )

    # Timeline toggle (dock)
    win.timeline_dock.toggleViewAction().setIcon(icon_timeline())

    # Custom overlay toggle: configurable via key 'custom' (falls back to 'layers' if missing)
    win.toggle_custom_action = QAction(get_icon("custom"), "Custom", win)
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
        "add_light": win.add_light_action,
    }

    # Load persisted shortcuts
    from ui.settings_keys import ORG, APP, SHORTCUT_KEY
    s = QSettings(ORG, APP)
    for key, action in win.shortcuts.items():
        seq = s.value(SHORTCUT_KEY(key))
        if seq:
            try:
                ks = QKeySequence(seq)
                if ks.isEmpty():
                    logger.warning("Ignoring invalid shortcut sequence for %s: %r", key, seq)
                else:
                    action.setShortcut(ks)
            except Exception as e:
                logger.warning("Failed to apply shortcut for %s: %r (%s)", key, seq, e)


def connect_signals(win: Any) -> None:
    """
    Wire UI actions and component signals to MainWindow slots.

    This function connects all the signals from the UI components to the
    appropriate slots in the MainWindow.

    Args:
        win: The MainWindow instance.
    """
    # Scene I/O
    win.save_action.triggered.connect(lambda: scene_io.save_scene(win))
    win.load_action.triggered.connect(lambda: scene_io.load_scene(win))
    win.reset_scene_action.triggered.connect(lambda: scene_actions.reset_scene(win))
    win.reset_ui_action.triggered.connect(win.reset_ui)
    win.settings_action.triggered.connect(win.open_settings_dialog)

    # Scene settings
    win.scene_size_action.triggered.connect(lambda: scene_actions.set_scene_size(win))
    win.background_action.triggered.connect(lambda: scene_actions.set_background(win))
    win.add_light_action.triggered.connect(
        lambda: win.scene_controller.create_light_object()
    )

    # ZoomableView signals
    win.view.zoom_requested.connect(win.scene_controller.zoom)
    win.view.fit_requested.connect(win.fit_to_view)
    win.view.handles_toggled.connect(win.toggle_rotation_handles)
    win.view.onion_toggled.connect(win.set_onion_enabled)
    win.view.item_dropped.connect(win.scene_controller.handle_library_drop)
    win.toggle_custom_action.toggled.connect(win.set_custom_overlay_visible)

    # PlaybackHandler signals
    win.playback_handler.snapshot_requested.connect(
        win.object_controller.snapshot_current_frame
    )
    win.playback_handler.frame_update_requested.connect(win.controller.on_frame_update)
    win.playback_handler.keyframe_add_requested.connect(win.controller.add_keyframe)

    # Library signals
    win.library_widget.addRequested.connect(
        win.scene_controller._add_library_item_to_scene
    )
