"""Module for synchronizing selection between the scene and the inspector."""

from __future__ import annotations

from typing import Any
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Qt


def select_object_in_inspector(win: Any, name: str) -> None:
    """Select the given object name in the inspector list, if present and visible.

    Keeps previous behavior: selects only 'object' entries matching name.
    """
    insp = getattr(win, 'inspector_widget', None)
    if not insp:
        return
    lw: QListWidget = insp.list_widget
    for i in range(lw.count()):
        it: QListWidgetItem = lw.item(i)
        typ, nm = it.data(Qt.UserRole)
        if typ == 'object' and nm == name:
            lw.setCurrentItem(it)
            break


def scene_selection_changed(win: Any) -> None:
    """When the scene selection changes, highlight the corresponding item in the inspector."""
    selected = win.scene.selectedItems()
    if not selected:
        return
    item = selected[0]
    for name, gi in win.object_manager.graphics_items.items():
        if gi is item and name in win.scene_model.objects:
            select_object_in_inspector(win, name)
            return

