import os
import sys
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_set_scene_size_updates_model_and_scene(app):
    win = MainWindow()
    win.scene_controller.set_scene_size(800, 600)
    assert win.scene_model.scene_width == 800
    assert win.scene_model.scene_height == 600
    rect = win.scene.sceneRect()
    assert rect.width() == 800
    assert rect.height() == 600
