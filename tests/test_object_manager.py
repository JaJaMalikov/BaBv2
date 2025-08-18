"""Tests for the ObjectManager class."""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    """Create a QApplication instance for the tests."""
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


def test_capture_visible_object_states(_app):
    """Test that the visible object states are captured correctly."""
    win = MainWindow()
    win.scene_controller.add_puppet(
        str(Path("assets/pantins/manu.svg").resolve()), "manu"
    )

    free_path = str(Path("assets/objets/Faucille.svg").resolve())
    # pylint: disable=protected-access
    free_name = win.scene_controller._create_object_from_file(free_path)
    free_item = win.object_manager.graphics_items[free_name]
    free_item.setPos(100.0, 200.0)

    attached_path = str(Path("assets/objets/Marteau.svg").resolve())
    # pylint: disable=protected-access
    attached_name = win.scene_controller._create_object_from_file(attached_path)
    win.scene_controller.attach_object_to_member(attached_name, "manu", "main_droite")
    attached_item = win.object_manager.graphics_items[attached_name]
    attached_item.setPos(10.0, 20.0)

    states = win.object_manager.capture_visible_object_states()

    free_state = states.get(free_name)
    attached_state = states.get(attached_name)
    assert free_state is not None and attached_state is not None
    assert free_state["attached_to"] in (None,)
    assert free_state["x"] == pytest.approx(100.0)
    assert free_state["y"] == pytest.approx(200.0)
    assert attached_state["attached_to"] == ("manu", "main_droite")
    assert attached_state["x"] == pytest.approx(10.0)
    assert attached_state["y"] == pytest.approx(20.0)
