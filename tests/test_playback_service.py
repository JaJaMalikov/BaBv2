"""Tests unitaires du ``PlaybackService``."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from controllers.playback_service import PlaybackService
from core.scene_model import SceneModel


@pytest.fixture()
def app():
    return QApplication.instance() or QApplication([])


def test_next_frame_advances_and_loops(app):  # noqa: ARG001
    model = SceneModel()
    service = PlaybackService(model)
    model.start_frame = 0
    model.end_frame = 2
    model.go_to_frame(0)
    service.next_frame()
    assert model.current_frame == 1
    service.loop_enabled = True
    model.go_to_frame(2)
    service.next_frame()
    assert model.current_frame == 0


def test_copy_paste_roundtrip(app):  # noqa: ARG001
    model = SceneModel()
    service = PlaybackService(model)
    state = {"objects": {"o1": {"pos": [1, 2]}}, "puppets": {}}
    model.add_keyframe(5, state)
    service.copy_keyframe(5)
    service.paste_keyframe(10)
    assert 10 in model.keyframes
    kf = model.keyframes[10]
    assert kf.objects == state["objects"]
    assert kf.puppets == state["puppets"]
