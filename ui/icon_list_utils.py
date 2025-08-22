"""Utility helpers for icon list widgets used in settings."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem


def populate_icon_list(
    lw: QListWidget,
    order_keys: list[str],
    visibility_map: dict[str, bool],
    specs: list[tuple[str, str, QIcon]],
) -> None:
    """Populate a ``QListWidget`` with icon items.

    Args:
        lw: The list widget to populate.
        order_keys: Ordered keys identifying items to add.
        visibility_map: Mapping of keys to visibility state.
        specs: Specifications for each icon (key, label, QIcon).
    """
    lw.clear()
    spec_map = {k: (label, icon) for (k, label, icon) in specs}
    for key in order_keys:
        if key not in spec_map:
            continue
        label, icon = spec_map[key]
        item = QListWidgetItem(icon, label)
        item.setData(Qt.UserRole, key)
        item.setFlags(
            item.flags()
            | Qt.ItemIsUserCheckable
            | Qt.ItemIsEnabled
            | Qt.ItemIsDragEnabled
            | Qt.ItemIsSelectable
        )
        item.setCheckState(Qt.Checked if visibility_map.get(key, True) else Qt.Unchecked)
        lw.addItem(item)


def extract_icon_list(lw: QListWidget) -> tuple[list[str], dict[str, bool]]:
    """Extract order and visibility information from ``QListWidget`` items."""
    order: list[str] = []
    vis: dict[str, bool] = {}
    for i in range(lw.count()):
        it = lw.item(i)
        key = it.data(Qt.UserRole)
        order.append(key)
        vis[key] = it.checkState() == Qt.Checked
    return order, vis
