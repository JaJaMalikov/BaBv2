"""Tests unitaires pour ``SceneService``."""

from __future__ import annotations


from typing import Dict

import pytest
from PySide6.QtWidgets import QApplication

from controllers.scene_service import SceneService
from core.scene_model import SceneModel


@pytest.fixture()
def app():
    return QApplication.instance() or QApplication([])


def _provider(state: Dict[str, Dict] | None = None):
    def _inner() -> Dict[str, Dict]:
        return state or {"puppets": {}, "objects": {}}

    return _inner


def test_add_keyframe_uses_provider(app):  # noqa: ARG001
    model = SceneModel()
    service = SceneService(model, _provider({"objects": {"o": {"x": 1}}, "puppets": {}}))
    service.add_keyframe(3)
    assert model.keyframes[3].objects["o"]["x"] == 1


def test_set_member_variant_creates_keyframe(app):  # noqa: ARG001
    model = SceneModel()
    service = SceneService(model, _provider())
    service.set_member_variant("p", "hand", "alt")
    kf = model.keyframes[0]
    assert kf.puppets["p"]["_variants"]["hand"] == "alt"


def test_background_and_size_signals(app):  # noqa: ARG001
    model = SceneModel()
    service = SceneService(model, _provider())
    bg_emitted: list[str | None] = []
    size_emitted: list[tuple[int, int]] = []
    service.background_changed.connect(lambda p: bg_emitted.append(p))
    service.scene_resized.connect(lambda w, h: size_emitted.append((w, h)))
    service.set_background_path("bg.png")
    service.set_scene_size(640, 480)
    assert model.background_path == "bg.png"
    assert model.scene_width == 640
    assert model.scene_height == 480
    assert bg_emitted == ["bg.png"]
    assert size_emitted == [(640, 480)]
