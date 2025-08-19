"""Validation helpers for scene JSON data.

This module provides light-weight checks used when importing a scene from
JSON. Each function validates part of the structure (global settings,
objects map or keyframes list) and logs descriptive errors when values do not
match the expected types.
"""

from __future__ import annotations

import logging
from typing import Any


def validate_settings(data: Any) -> bool:
    """Validate scene settings structure.

    ``data`` should be a mapping of setting keys to integer values. Unknown keys
    are ignored. ``None`` is accepted and treated as valid to allow optional
    sections in the JSON.

    Hardened checks (docs/tasks.md Task 4.25):
    - Numeric settings must be integers and non-negative.
    - If both start_frame and end_frame are provided, start_frame <= end_frame.
    - background_path, when present, must be a string.
    """
    if data is None:
        return True
    if not isinstance(data, dict):
        logging.error("settings: expected dict, got %s", type(data).__name__)
        return False
    for key in ("start_frame", "end_frame", "fps", "scene_width", "scene_height"):
        if key in data:
            if not isinstance(data[key], int):
                logging.error("settings: %s must be int", key)
                return False
            if data[key] < 0:
                logging.error("settings: %s must be non-negative", key)
                return False
    if "start_frame" in data and "end_frame" in data and data["start_frame"] > data["end_frame"]:
        logging.error("settings: start_frame must be <= end_frame")
        return False
    if "background_path" in data and data["background_path"] is not None and not isinstance(data["background_path"], str):
        logging.error("settings: background_path must be a string or null")
        return False
    return True


def validate_objects(data: Any) -> bool:
    """Validate objects mapping structure.

    ``data`` should map object names (strings) to dictionaries describing their
    state. ``None`` is accepted as a valid value meaning no objects.
    """
    if data is None:
        return True
    if not isinstance(data, dict):
        logging.error(
            "objects: expected dict mapping str -> dict, got %s", type(data).__name__
        )
        return False
    for name, obj in data.items():
        if not isinstance(name, str) or not isinstance(obj, dict):
            logging.error("objects: invalid entry %r -> %r", name, obj)
            return False
    return True


def validate_keyframes(data: Any) -> bool:
    """Validate keyframes list structure.

    ``data`` should be a list of dictionaries, each containing an optional
    integer ``index``.
    """
    if data is None:
        return True
    if not isinstance(data, list):
        logging.error("keyframes: expected list, got %s", type(data).__name__)
        return False
    for kf in data:
        if not isinstance(kf, dict):
            logging.error("keyframes: each item must be dict, got %r", kf)
            return False
        idx = kf.get("index")
        if idx is not None and not isinstance(idx, int):
            logging.error("keyframes: 'index' must be int, got %r", idx)
            return False
    return True
