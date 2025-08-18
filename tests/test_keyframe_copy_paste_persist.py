"""End-to-end tests for keyframe copy/paste and export/import persistence.

These tests exercise the TimelineWidget signals, PlaybackHandler, SceneModel,
and scene import/export to ensure the pasted keyframe is identical to the copied
one and survives a full save+load roundtrip.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.scene import scene_io


@pytest.fixture(scope="module")
def app():
    app = QApplication.instance() or QApplication([])
    return app


def _state_at(win: MainWindow, idx: int) -> tuple[dict, dict]:
    kf = win.scene_model.keyframes.get(idx)
    assert kf is not None, f"Missing keyframe at {idx}"
    return kf.puppets, kf.objects


def _semantic_puppet_state(win: MainWindow, puppets_state: dict) -> dict:
    """Reduce puppet state to a semantic subset stable across import/export.

    Keeps per-member rotation, root member pos, and _variants selection.
    """
    out: dict = {}
    for pname, pstate in puppets_state.items():
        pup = win.scene_model.puppets.get(pname)
        if not pup:
            continue
        root_names = {m.name for m in pup.get_root_members()}
        reduced: dict = {}
        for mname, mstate in pstate.items():
            if mname == "_variants":
                reduced[mname] = dict(mstate)
                continue
            if not isinstance(mstate, dict):
                continue
            r: dict = {}
            if "rotation" in mstate:
                r["rotation"] = float(mstate["rotation"])
            if mname in root_names and "pos" in mstate:
                pos = mstate.get("pos")
                if isinstance(pos, (list, tuple)) and len(pos) == 2:
                    r["pos"] = [float(pos[0]), float(pos[1])]
            if r:
                reduced[mname] = r
        out[pname] = reduced
    return out


def _add_default_puppet(win: MainWindow, name: str = "manu") -> None:
    svg = Path("assets/pantins/manu.svg")
    assert svg.exists(), "Missing default puppet SVG for test"
    win.scene_controller.add_puppet(str(svg), name)


def test_copy_paste_then_export_import_persists(app, tmp_path: Path):  # noqa: ARG001
    win = MainWindow()
    _add_default_puppet(win)

    # Build a source keyframe @ 5 by snapshotting visible state
    win.timeline_widget.set_current_frame(5)
    win.object_manager.snapshot_current_frame()
    assert 5 in win.scene_model.keyframes

    # Copy via handler
    win.playback_handler.copy_keyframe(5)

    # Paste via handler into 20 and ensure scene updated
    win.playback_handler.paste_keyframe(20)
    assert 20 in win.scene_model.keyframes

    src_pup, src_obj = _state_at(win, 5)
    dst_pup, dst_obj = _state_at(win, 20)
    # Compare semantic puppet state (rotations, root pos, variants)
    assert _semantic_puppet_state(win, dst_pup) == _semantic_puppet_state(win, src_pup)
    # Objects: exact compare is acceptable here (position/rotation/scale/z)
    assert dst_obj == src_obj

    # Export to JSON
    scene_path = tmp_path / "scene_copy_paste.json"
    scene_io.export_scene(win, str(scene_path))
    assert scene_path.exists()

    # Import in a clean window
    win2 = MainWindow()
    scene_io.import_scene(win2, str(scene_path))
    assert 20 in win2.scene_model.keyframes
    pup2, obj2 = _state_at(win2, 20)
    assert _semantic_puppet_state(win2, pup2) == _semantic_puppet_state(win, src_pup)
    assert obj2 == src_obj


def test_copy_paste_via_signals_matches_handler(app):  # noqa: ARG001
    win = MainWindow()
    _add_default_puppet(win)

    # Seed a keyframe @ 7
    win.timeline_widget.set_current_frame(7)
    win.object_manager.snapshot_current_frame()
    assert 7 in win.scene_model.keyframes

    # Copy via timeline signal
    win.timeline_widget.copyKeyframeClicked.emit(7)

    # Paste via timeline signal at 23
    win.timeline_widget.pasteKeyframeClicked.emit(23)
    assert 23 in win.scene_model.keyframes
    pup7, obj7 = _state_at(win, 7)
    pup23, obj23 = _state_at(win, 23)
    assert _semantic_puppet_state(win, pup23) == _semantic_puppet_state(win, pup7)
    assert obj23 == obj7


def test_paste_on_current_frame_overwrites_correctly(app):  # noqa: ARG001
    """Verify that pasting onto the current frame correctly uses the clipboard.

    This specifically tests the bug where pasting on the current frame would
    incorrectly re-snapshot the old state instead of the pasted one.
    """
    win = MainWindow()
    _add_default_puppet(win)

    # Create a keyframe at frame 5 with a specific rotation
    win.timeline_widget.set_current_frame(5)
    torso = win.object_manager.graphics_items["manu:torse"]
    torso.rotate_piece(30)  # A specific state for frame 5
    win.object_manager.snapshot_current_frame()
    assert 5 in win.scene_model.keyframes
    pup5, obj5 = _state_at(win, 5)
    assert pup5["manu"]["torse"]["rotation"] == 30

    # Create a different keyframe at frame 10
    win.timeline_widget.set_current_frame(10)
    torso.rotate_piece(0)  # A different state for frame 10
    win.object_manager.snapshot_current_frame()
    assert 10 in win.scene_model.keyframes
    pup10_original, _ = _state_at(win, 10)
    assert pup10_original["manu"]["torse"]["rotation"] == 0

    # 1. Copy state from frame 5
    win.playback_handler.copy_keyframe(5)

    # 2. Ensure we are on frame 10
    win.timeline_widget.set_current_frame(10)
    assert win.scene_model.current_frame == 10

    # 3. Paste (which should overwrite frame 10)
    win.playback_handler.paste_keyframe(10)

    # 4. Verify the state at frame 10 is now the one from frame 5
    pup10_pasted, obj10_pasted = _state_at(win, 10)

    # Use semantic compare for puppets
    assert _semantic_puppet_state(win, pup10_pasted) == _semantic_puppet_state(
        win, pup5
    )
    # Objects should be identical
    assert obj10_pasted == obj5
    # And specifically check the rotation that we set
    assert pup10_pasted["manu"]["torse"]["rotation"] == 30
