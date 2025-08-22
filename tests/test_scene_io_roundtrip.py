"""Tests for Scene IO round-trip with puppets_data.

Covers exporting a scene with a puppet (scale/position/rotation/z_offset)
then re-importing and asserting state is reapplied. Also includes a case where
puppet path is missing, which should be skipped gracefully.
"""

from __future__ import annotations

from pathlib import Path
import json

import pytest
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.scene import scene_io


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def _add_default_puppet(win: MainWindow, name: str = "manu") -> str:
    svg = Path("assets/pantins/manu.svg")
    assert svg.exists(), "Missing default puppet SVG for test"
    win.scene_controller.add_puppet(str(svg), name)
    return str(svg)


def _root_piece(win: MainWindow, puppet_name: str):
    pup = win.scene_model.puppets.get(puppet_name)
    assert pup is not None, f"Puppet {puppet_name} not found"
    roots = pup.get_root_members()
    assert roots, "Puppet has no root members"
    key = f"{puppet_name}:{roots[0].name}"
    return win.object_manager.graphics_items.get(key)


def test_roundtrip_puppets_data_reapplies_state(app, tmp_path: Path):  # noqa: ARG001
    win = MainWindow()
    name = "manu"
    _add_default_puppet(win, name)

    # Adjust puppet transform state in the live scene
    win.scene_controller.scale_puppet(name, 1.5)
    win.object_manager.puppet_scales[name] = 1.5  # Explicitly store absolute scale
    win.scene_controller.set_puppet_rotation(name, 45.0)
    win.scene_controller.set_puppet_z_offset(name, 7)

    root = _root_piece(win, name)
    assert root is not None
    root.setPos(12.0, 34.0)

    # Snapshot state to ensure it's captured before export
    win.object_controller.snapshot_current_frame()

    # Export
    scene_path = tmp_path / "scene_with_puppet.json"
    scene_io.export_scene(win, str(scene_path))
    assert scene_path.exists()

    # Import into fresh window
    win2 = MainWindow()
    scene_io.import_scene(win2, str(scene_path))

    # Puppet should be present
    assert name in win2.scene_model.puppets

    # Scale reapplied
    assert pytest.approx(1.5, rel=1e-6) == win2.object_manager.puppet_scales.get(name)

    # Rotation reapplied
    assert pytest.approx(45.0, rel=1e-6) == win2.scene_controller.get_puppet_rotation(
        name
    )

    # Z offset reapplied
    assert win2.object_manager.puppet_z_offsets.get(name) == 7

    # Position reapplied on root piece
    root2 = _root_piece(win2, name)
    assert root2 is not None
    pos = root2.pos()
    assert pytest.approx(12.0, rel=1e-6) == pos.x()
    assert pytest.approx(34.0, rel=1e-6) == pos.y()


def test_import_skips_missing_puppet_path(app, tmp_path: Path):  # noqa: ARG001
    win = MainWindow()
    name = "manu"
    _add_default_puppet(win, name)

    # Export normally
    scene_path = tmp_path / "scene_missing_path.json"
    scene_io.export_scene(win, str(scene_path))

    # Rewrite JSON to simulate missing puppet asset path for manu
    data = json.loads(scene_path.read_text(encoding="utf-8"))
    assert "puppets_data" in data
    data["puppets_data"][name]["path"] = str(tmp_path / "does_not_exist.svg")
    broken_path = tmp_path / "scene_missing_path_broken.json"
    broken_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Import into fresh window - should not raise and should skip puppet
    win2 = MainWindow()
    scene_io.import_scene(win2, str(broken_path))

    # Puppet should not be present since path doesn't exist
    assert name not in win2.scene_model.puppets

    # Import should continue and set up timeline/scene without crashing
    # e.g., ensure keyframes mapping exists and scene rect set
    assert isinstance(win2.scene_model.keyframes, dict)
    rect = win2.scene.sceneRect()
    assert rect.width() > 0 and rect.height() > 0
