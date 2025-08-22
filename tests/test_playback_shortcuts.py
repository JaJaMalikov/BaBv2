"""Tests for shortcut-driven copy/paste robustness via AppController.

Covers docs/tasks.md Task 18:
- Shortcut-driven copy/paste current keyframe through AppController
- Graceful no-op behavior when no keyframe/clipboard exists
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def test_shortcuts_no_keyframe_noop(_app):  # noqa: ARG001
    """Copy/paste via AppController should be no-ops when nothing is available.

    Ensures there are no exceptions and no keyframes are created implicitly.
    """
    win = MainWindow()
    # Sanity: no keyframes at start
    assert not win.scene_model.keyframes

    # Invoke shortcut handlers (no active keyframe/clipboard)
    win.controller.copy_current_keyframe()
    win.controller.paste_current_keyframe()
    QApplication.processEvents()

    # Still no keyframes
    assert not win.scene_model.keyframes


def test_shortcuts_copy_paste_roundtrip(_app):  # noqa: ARG001
    """End-to-end copy/paste through AppController methods.

    - Seed a keyframe by snapshotting current frame
    - Mark the keyframe on the timeline (so AppController.copy guard passes)
    - Copy via AppController, move to another frame, paste via AppController
    - Verify the destination keyframe exists and matches source state
    """
    win = MainWindow()

    # Add default puppet to ensure a meaningful snapshot state
    svg = Path("assets/pantins/manu.svg")
    assert svg.exists(), "Missing default puppet SVG for test"
    win.scene_controller.add_puppet(str(svg), "manu")

    # Create a source keyframe @ 5 by snapshotting visible state
    win.timeline_widget.set_current_frame(5)
    win.object_controller.snapshot_current_frame()
    assert 5 in win.scene_model.keyframes

    # Ensure the timeline has a marker so AppController.copy_current_keyframe proceeds
    win.timeline_widget.add_keyframe_marker(5)

    # Copy via AppController (shortcut path)
    win.controller.copy_current_keyframe()

    # Paste onto a different frame via AppController (shortcut path)
    win.timeline_widget.set_current_frame(12)
    win.controller.paste_current_keyframe()

    assert 12 in win.scene_model.keyframes

    kf5 = win.scene_model.keyframes[5]
    kf12 = win.scene_model.keyframes[12]
    assert kf12.objects == kf5.objects
    assert kf12.puppets == kf5.puppets
