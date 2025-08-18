"""Tests for the SceneController class."""

import pytest
from PySide6.QtWidgets import QApplication

from ui.scene import SceneController
from ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    """Create a QApplication instance for the tests."""
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


def test_set_scene_size_updates_scene(_app):
    """The controller updates the graphics view size."""
    win = MainWindow()
    assert isinstance(win.scene_controller, SceneController)
    win.scene_controller.set_scene_size(800, 600)
    rect = win.scene.sceneRect()
    assert rect.width() == 800
    assert rect.height() == 600
