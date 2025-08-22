from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.scene import scene_io


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_export_puppet_paths_relative(app, tmp_path: Path):  # noqa: ARG001
    win = MainWindow()
    name = "manu"

    # Add default puppet from assets
    svg = Path("assets/pantins/manu.svg")
    assert svg.exists(), "Missing default puppet SVG for test"
    win.scene_controller.add_puppet(str(svg), name)

    # Ensure there's at least one keyframe
    if not win.scene_model.keyframes:
        win.controller.add_keyframe(0)

    scene_path = tmp_path / "scene_paths.json"
    scene_io.export_scene(win, str(scene_path))

    data = scene_path.read_text(encoding="utf-8")
    import json

    payload = json.loads(data)
    assert "puppets_data" in payload and name in payload["puppets_data"]

    pd = payload["puppets_data"][name]
    rel = pd.get("path")
    abs_hint = pd.get("abs_path")

    assert rel, "Expected a relative path in puppets_data.path"
    assert not os.path.isabs(rel), "Exported puppet path should be relative"
    assert abs_hint and os.path.isabs(abs_hint), "abs_path hint should be absolute"

    # Verify that resolving the relative path against the scene directory points to an existing file
    scene_dir = scene_path.parent
    resolved = (scene_dir / rel).resolve()
    assert resolved.exists(), f"Resolved relative path does not exist: {resolved}"
