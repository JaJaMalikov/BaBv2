"""Tests for scene validation helpers."""

import logging

from core.scene_validation import (
    validate_settings,
    validate_objects,
    validate_keyframes,
)


def test_validate_settings(caplog):
    """Settings must be dict with integer values."""
    assert validate_settings({"fps": 24, "scene_width": 800}) is True
    with caplog.at_level(logging.ERROR):
        assert validate_settings({"fps": "fast"}) is False
        assert "fps" in caplog.text


def test_validate_objects(caplog):
    """Objects must map names to dicts."""
    assert validate_objects({"tree": {}}) is True
    with caplog.at_level(logging.ERROR):
        assert validate_objects({"tree": []}) is False
        assert "invalid entry" in caplog.text


def test_validate_keyframes(caplog):
    """Keyframes must be list of dict with integer index."""
    assert validate_keyframes([{"index": 1}]) is True
    with caplog.at_level(logging.ERROR):
        assert validate_keyframes([{"index": "a"}]) is False
        assert "index" in caplog.text
