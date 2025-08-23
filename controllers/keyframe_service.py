from __future__ import annotations

"""Utilities for keyframe copy/paste operations.

Centralizes the keyframe clipboard semantics to avoid logic duplication across
controllers. This module is Qt-free and depends only on the SceneModel surface.
"""
from copy import deepcopy
from typing import Any, Dict, Optional


def copy_keyframe(model: Any, index: int) -> Optional[Dict[str, Any]]:
    """Return a clipboard dict for the keyframe at ``index`` or None if missing.

    Structure: {"objects": dict, "puppets": dict, "source_index": int}
    Uses deepcopy when possible to avoid accidental aliasing.
    """
    kf = getattr(model, "keyframes", {}).get(int(index))
    if not kf:
        return None
    try:
        return {
            "objects": deepcopy(kf.objects),
            "puppets": deepcopy(kf.puppets),
            "source_index": int(index),
        }
    except Exception:
        return {
            "objects": dict(getattr(kf, "objects", {})),
            "puppets": dict(getattr(kf, "puppets", {})),
            "source_index": int(index),
        }


def paste_keyframe(model: Any, clipboard: Optional[Dict[str, Any]], index: int) -> bool:
    """Apply ``clipboard`` at ``index`` into ``model``.

    Returns True if anything was pasted, False otherwise.
    """
    if not clipboard:
        return False
    state = {
        "objects": clipboard.get("objects", {}),
        "puppets": clipboard.get("puppets", {}),
    }
    model.add_keyframe(int(index), state)
    return True
