"""Module for synchronizing selection between the scene and the inspector."""

from __future__ import annotations

from typing import Any
import logging
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


def select_object_in_inspector(win: Any, name: str) -> None:
    """Select the given object name in the inspector list, if present and visible.

    Keeps previous behavior: selects only 'object' entries matching name.
    """
    insp = getattr(win, "inspector_widget", None)
    if not insp or not hasattr(insp, "list_widget"):
        logger.debug("Inspector widget or list not available; skipping selection")
        return
    lw = getattr(insp, "list_widget", None)
    if not isinstance(lw, QListWidget):
        return
    for i in range(lw.count()):
        it: QListWidgetItem = lw.item(i)
        data = it.data(Qt.UserRole)
        if not isinstance(data, (tuple, list)) or len(data) < 2:
            continue
        typ, nm = data[0], data[1]
        if typ == "object" and nm == name:
            lw.setCurrentItem(it)
            break


def scene_selection_changed(win: Any) -> None:
    """When the scene selection changes, highlight the corresponding item in the inspector."""
    scene = getattr(win, "scene", None)
    if scene is None or not hasattr(scene, "selectedItems"):
        return
    selected = scene.selectedItems() or []
    if not selected:
        return
    item = selected[0]
    obj_mgr = getattr(win, "object_manager", None)
    scene_model = getattr(win, "scene_model", None)
    if not obj_mgr or not scene_model or not hasattr(obj_mgr, "graphics_items"):
        return
    for name, gi in obj_mgr.graphics_items.items():
        if gi is item and name in scene_model.objects:
            select_object_in_inspector(win, name)
            return
