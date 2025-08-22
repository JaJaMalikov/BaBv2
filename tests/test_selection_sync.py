"""Tests for inspector and scene selection synchronization via AppController.

Covers:
- AppController.select_object_in_inspector selects the object in Inspector.
- AppController.on_scene_selection_changed reacts to QGraphicsScene selection and
  updates Inspector accordingly.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def _create_simple_object(win: MainWindow) -> str:
    asset = Path("assets/objets/faucille.svg")
    assert asset.exists(), "Test asset not found: assets/objets/faucille.svg"
    name = win.object_controller.create_object_from_file(str(asset))
    assert name is not None
    # Ensure inspector list reflects new object
    win.inspector_widget.refresh()
    return name


def test_select_object_in_inspector_via_app_controller(_app):  # noqa: ARG001
    win = MainWindow()
    name = _create_simple_object(win)

    # Exercise controller API
    win.controller.select_object_in_inspector(name)
    QApplication.processEvents()

    item = win.inspector_widget.list_widget.currentItem()
    assert item is not None, "Inspector should have a current item after selection"
    typ, nm = (
        item.data(item.dataRole()) if hasattr(item, "dataRole") else item.data(32)
    ), None  # fallback
    # Qt.UserRole == 0x100 (256); QListWidgetItem.data uses role constant; use API to fetch
    from PySide6.QtCore import Qt

    typ, nm = item.data(Qt.UserRole)
    assert typ == "object" and nm == name
    assert win.inspector_widget.props_panel.isVisible()


def test_on_scene_selection_changed_updates_inspector(_app):  # noqa: ARG001
    win = MainWindow()
    name = _create_simple_object(win)

    # Select the graphics item in the scene directly
    gi = win.object_manager.graphics_items.get(name)
    assert gi is not None and gi.isVisible()
    gi.setSelected(True)

    # Let the controller handle the scene selection change
    win.controller.on_scene_selection_changed()
    QApplication.processEvents()

    item = win.inspector_widget.list_widget.currentItem()
    assert item is not None
    from PySide6.QtCore import Qt

    typ, nm = item.data(Qt.UserRole)
    assert typ == "object" and nm == name
