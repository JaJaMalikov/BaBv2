from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from controllers.playback_service import PlaybackService
from core.scene_model import SceneModel


@pytest.fixture()
def app():
    return QApplication.instance() or QApplication([])


def test_playback_signals_exist_and_snake_case(app):  # noqa: ARG001
    service = PlaybackService(SceneModel())
    # check attributes exist and are Qt signals (have emit method)
    for name in (
        "frame_update_requested",
        "keyframe_add_requested",
        "snapshot_requested",
        "current_frame_changed",
    ):
        sig = getattr(service, name, None)
        assert sig is not None, f"Missing signal: {name}"
        assert hasattr(sig, "emit"), f"Signal {name} should have emit()"


def test_set_fps_updates_timer_interval(app):  # noqa: ARG001
    service = PlaybackService(SceneModel())
    service.set_fps(25)
    assert service.playback_timer.interval() == 40  # 1000 // 25
    service.set_fps(0)
    assert service.playback_timer.interval() == 0
