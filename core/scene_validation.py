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

    Additional constraints (docs/tasks.md Task 16):
    - fps > 0 when present
    - scene_width > 0 and scene_height > 0 when present
    - start_frame <= end_frame when both present
    """
    if data is None:
        return True
    if not isinstance(data, dict):
        logging.error("settings: expected dict, got %s", type(data).__name__)
        return False
    for key in ("start_frame", "end_frame", "fps", "scene_width", "scene_height"):
        if key in data and not isinstance(data[key], int):
            logging.error("settings: %s must be int", key)
            return False
    # Semantic checks
    if "fps" in data:
        if data["fps"] <= 0:
            logging.error("settings: fps must be > 0, got %r", data["fps"])
            return False
    if "scene_width" in data:
        if data["scene_width"] <= 0:
            logging.error("settings: scene_width must be > 0, got %r", data["scene_width"])
            return False
    if "scene_height" in data:
        if data["scene_height"] <= 0:
            logging.error("settings: scene_height must be > 0, got %r", data["scene_height"])
            return False
    if "start_frame" in data and "end_frame" in data:
        if data["start_frame"] > data["end_frame"]:
            logging.error(
                "settings: start_frame (%r) must be <= end_frame (%r)",
                data["start_frame"],
                data["end_frame"],
            )
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

    Additional constraints (docs/tasks.md Task 17):
    - If provided, ``index`` must be an integer and unique across the list.
    """
    if data is None:
        return True
    if not isinstance(data, list):
        logging.error("keyframes: expected list, got %s", type(data).__name__)
        return False
    seen: set[int] = set()
    for kf in data:
        if not isinstance(kf, dict):
            logging.error("keyframes: each item must be dict, got %r", kf)
            return False
        idx = kf.get("index")
        if idx is not None and not isinstance(idx, int):
            logging.error("keyframes: 'index' must be int, got %r", idx)
            return False
        if isinstance(idx, int):
            if idx in seen:
                logging.error("keyframes: duplicate index %r", idx)
                return False
            seen.add(idx)
    return True
