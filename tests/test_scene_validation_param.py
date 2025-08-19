"""Additional parameterized tests for scene validation helpers.

Covers more valid/invalid combinations for settings to increase coverage
and demonstrate parametrization (docs/tasks.md Task 12).
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import pytest

from core.scene_validation import validate_settings


@pytest.mark.parametrize(
    "settings, expected_ok, contains",
    [
        ({"start_frame": 0, "end_frame": 0, "fps": 24}, True, None),
        (
            {"start_frame": 0, "end_frame": 10, "fps": 12, "scene_width": 800, "scene_height": 600},
            True,
            None,
        ),
        ({"start_frame": 5, "end_frame": 1}, False, "start_frame"),  # start > end
        ({"fps": -1}, False, "non-negative"),  # negative disallowed
        ({"background_path": 123}, False, "background_path"),  # wrong type
        (None, True, None),  # optional section allowed
        ("oops", False, "expected dict"),  # wrong container type
    ],
)
def test_validate_settings_param(
    caplog: pytest.LogCaptureFixture,
    settings: Dict[str, Any] | None,
    expected_ok: bool,
    contains: str | None,
) -> None:
    with caplog.at_level(logging.ERROR):
        ok = validate_settings(settings)
    assert ok is expected_ok
    if contains is not None:
        assert contains in caplog.text
