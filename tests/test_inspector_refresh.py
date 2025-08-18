"""Tests ensuring the inspector widget stays in sync with scene objects."""

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


def test_inspector_lists_new_objects(_app) -> None:
    """Adding objects should refresh the inspector automatically."""
    win = MainWindow()
    assert win.inspector_widget.list_widget.count() == 0

    obj_path = str(Path("assets/objets/Faucille.svg").resolve())
    # pylint: disable=protected-access
    name = win.scene_controller._create_object_from_file(obj_path)

    items = [
        win.inspector_widget.list_widget.item(i).text()
        for i in range(win.inspector_widget.list_widget.count())
    ]
    assert name in items

    win.scene_controller.create_light_object()
    items = [
        win.inspector_widget.list_widget.item(i).text()
        for i in range(win.inspector_widget.list_widget.count())
    ]
    assert any("projecteur" in it for it in items)
