from ui.scene import SceneController
"""Tests for the SceneController class."""

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


def test_set_scene_size_updates_model_and_scene(_app):
    """Test that setting the scene size updates the model and the scene."""
    win = MainWindow()
    assert isinstance(win.scene_controller, SceneController)
    win.scene_controller.set_scene_size(800, 600)
    assert win.scene_model.scene_width == 800
    assert win.scene_model.scene_height == 600
    rect = win.scene.sceneRect()
    assert rect.width() == 800
    assert rect.height() == 600
