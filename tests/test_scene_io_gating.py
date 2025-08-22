import pytest
from PySide6.QtWidgets import QFileDialog

from ui.scene.scene_io import save_scene, load_scene


def test_save_load_scene_dialogs_gated(monkeypatch, _app):
    # Force gating off for dialogs
    import ui.scene.scene_io as sio

    monkeypatch.setattr(sio, "ALLOW_FILE_DIALOGS", False, raising=False)

    # Make QFileDialog methods raise if they are called (they should not be)
    def _fail(*args, **kwargs):
        raise AssertionError("QFileDialog should not be invoked when ALLOW_FILE_DIALOGS=False")

    monkeypatch.setattr(QFileDialog, "getSaveFileName", _fail, raising=False)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", _fail, raising=False)

    # Call API with a dummy window object; it won't be used under gating
    save_scene(object())
    load_scene(object())
