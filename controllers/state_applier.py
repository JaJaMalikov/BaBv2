from __future__ import annotations

"""Controller-side single entry point to apply model state to the scene.

Keeps views purely visual by delegating to the SceneController/StateApplier
pipeline while providing a stable function for controllers to call.
"""
from typing import Any, Dict


def apply_frame(win: Any) -> None:
    """Apply the current frame state from the model to scene graphics.

    Expects ``win`` to satisfy AppWindowContract-like attributes:
    - scene_controller: has apply_puppet_states/apply_object_states
    - object_view_adapter.graphics_items: mapping of object names -> items
    - scene_model.keyframes/current_frame
    """
    index: int = int(win.scene_model.current_frame)
    keyframes: Dict[int, Any] = win.scene_model.keyframes
    if not keyframes:
        return
    graphics_items: Dict[str, Any] = win.object_view_adapter.graphics_items
    win.scene_controller.apply_puppet_states(graphics_items, keyframes, index)
    win.scene_controller.apply_object_states(graphics_items, keyframes, index)
