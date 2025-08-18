"""Tests for object keyframe states."""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QGraphicsItem

from ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    """Create a QApplication instance for the tests."""
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


def _puppet_piece(win: MainWindow, puppet: str, member: str):
    return win.object_manager.graphics_items.get(f"{puppet}:{member}")


def test_object_state_is_per_keyframe(_app):
    """Test that object state is correctly saved and restored per keyframe."""
    win = MainWindow()

    win.scene_controller.add_puppet(
        str(Path("assets/pantins/manu.svg").resolve()), "manu"
    )

    # Ensure on frame 0
    win.playback_handler.go_to_frame(0)

    # Create a free object at a known position
    obj_path = str(Path("assets/objets/Faucille.svg").resolve())
    # pylint: disable=protected-access
    name = win.scene_controller._create_object_from_file(obj_path)
    assert name in win.object_manager.graphics_items
    item = win.object_manager.graphics_items[name]

    # Move free object to a scene position and snapshot on KF 0
    item.setPos(123.0, 234.0)
    win.controller.add_keyframe(0)
    win.object_manager.snapshot_current_frame()

    # Attach the object at KF 0 and set a local offset, re-snapshot
    win.scene_controller.attach_object_to_member(name, "manu", "main_droite")
    item.setPos(10.0, 20.0)  # local pos relative to the member
    win.object_manager.snapshot_current_frame()

    # Jump to frame 10, detach and set a different scene position, snapshot
    win.playback_handler.go_to_frame(10)
    win.controller.add_keyframe(10)
    win.scene_controller.detach_object(name)
    item = win.object_manager.graphics_items[name]
    assert item.parentItem() is None
    item.setPos(345.0, 456.0)
    win.object_manager.snapshot_current_frame()

    # Validate states in keyframes
    kf0 = win.scene_model.keyframes.get(0)
    kf10 = win.scene_model.keyframes.get(10)
    assert kf0 is not None and kf10 is not None
    st0 = kf0.objects.get(name)
    st10 = kf10.objects.get(name)
    assert st0 is not None and st10 is not None

    # Frame 0: attached with expected local position
    assert st0.get("attached_to") == ("manu", "main_droite")
    assert st0.get("x") == pytest.approx(10.0)
    assert st0.get("y") == pytest.approx(20.0)

    # Frame 10: free with expected scene position
    assert st10.get("attached_to") in (None,)
    assert st10.get("x") == pytest.approx(345.0)
    assert st10.get("y") == pytest.approx(456.0)

    # Now, ensure that applying states restores correct parent/positions
    win.playback_handler.go_to_frame(0)
    win.controller.update_scene_from_model()
    item0 = win.object_manager.graphics_items[name]
    assert isinstance(item0.parentItem(), QGraphicsItem)
    # Parent is the puppet piece for manu:main_droite
    parent_piece = _puppet_piece(win, "manu", "main_droite")
    assert item0.parentItem() is parent_piece
    assert item0.x() == pytest.approx(10.0)
    assert item0.y() == pytest.approx(20.0)

    win.playback_handler.go_to_frame(10)
    win.controller.update_scene_from_model()
    item10 = win.object_manager.graphics_items[name]
    assert item10.parentItem() is None
    assert item10.x() == pytest.approx(345.0)
    assert item10.y() == pytest.approx(456.0)
