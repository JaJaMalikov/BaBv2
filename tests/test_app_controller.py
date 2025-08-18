"""Tests unitaires pour ``AppController``."""

from controllers.app_controller import AppController
from controllers.scene_service import SceneService
from core.scene_model import SceneModel


class _DummyTimeline:
    """Widget factice enregistrant les marqueurs de keyframe."""

    def __init__(self) -> None:
        self.markers: list[int] = []

    def add_keyframe_marker(self, frame_index: int) -> None:
        self.markers.append(int(frame_index))


class _DummySceneController:
    """SceneController minimal exposant un ``SceneService``."""

    def __init__(self, model: SceneModel) -> None:
        self.service = SceneService(model, lambda: {"puppets": {}, "objects": {}})


class _DummyWindow:
    """Fenêtre minimale utilisée par ``AppController``."""

    def __init__(self) -> None:
        self.scene_model = SceneModel()
        self.timeline_widget = _DummyTimeline()
        self.scene_controller = _DummySceneController(self.scene_model)


def test_add_keyframe_updates_model() -> None:
    win = _DummyWindow()
    ctrl = AppController(win)
    ctrl.add_keyframe(5)
    assert 5 in win.scene_model.keyframes
    assert win.timeline_widget.markers == [5]
