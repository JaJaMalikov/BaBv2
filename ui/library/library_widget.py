"""Library panel showing background, objects and puppets available under assets/.

Provides drag-and-drop payloads and context menu to add items to the scene.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QMimeData, QByteArray, Signal, QPoint, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QTabWidget,
)
from PySide6.QtGui import QDrag, QIcon

from ui.icons import get_icon

LIB_MIME = "application/x-bab-item"


class _DraggableGrid(QListWidget):
    """Grid widget that provides drag and drop with contextual actions."""

    addRequested = Signal(dict)

    # Qt widgets often expose only a couple of public methods
    # which triggers ``too-few-public-methods``.
    # pylint: disable=too-few-public-methods

    def __init__(self, parent=None):
        """Initialise the grid widget."""
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragOnly)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_context_menu)

        # Grid / Icon settings
        self.setViewMode(QListWidget.IconMode)
        self.setResizeMode(QListWidget.Adjust)
        self.setMovement(QListWidget.Static)
        self.setIconSize(QSize(96, 96))
        self.setGridSize(QSize(112, 120))
        self.setWordWrap(True)

    def startDrag(self, _supported_actions):  # pylint: disable=invalid-name
        """Start a drag operation with the current item."""
        item = self.currentItem()
        if not item:
            return
        payload = item.data(Qt.UserRole)
        if not payload:
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(LIB_MIME, QByteArray(json.dumps(payload).encode("utf-8")))
        pixmap = item.icon().pixmap(self.iconSize())
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        drag.exec(Qt.CopyAction)

    def _open_context_menu(self, pos: QPoint):
        """Display a context menu to add the item to the scene."""
        item = self.itemAt(pos)
        if not item:
            return
        payload = item.data(Qt.UserRole)
        if not payload:
            return
        menu = QMenu(self)
        act_add = menu.addAction("Ajouter à la scène")
        action = menu.exec(self.viewport().mapToGlobal(pos))
        if action == act_add:
            self.addRequested.emit(payload)

    def mouseDoubleClickEvent(self, event):  # pylint: disable=invalid-name
        """Emit the payload when an item is double-clicked."""
        item = self.itemAt(event.position().toPoint())
        if item:
            payload = item.data(Qt.UserRole)
            if payload:
                self.addRequested.emit(payload)
                event.accept()
                return
        super().mouseDoubleClickEvent(event)


class LibraryWidget(QWidget):  # pylint: disable=too-few-public-methods
    """Widget listing available assets for drag and drop."""

    addRequested = Signal(dict)

    def __init__(self, root_dir: Optional[str] = None, parent=None):
        """Initialise the library widget."""
        super().__init__(parent)
        self.root_dir = Path(root_dir or ".").resolve()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setIconSize(QSize(32, 32))

        # Create a grid for each category
        self.background_grid = _DraggableGrid()
        self.objects_grid = _DraggableGrid()
        self.puppets_grid = _DraggableGrid()

        # Connect signals
        self.background_grid.addRequested.connect(self.addRequested)
        self.objects_grid.addRequested.connect(self.addRequested)
        self.puppets_grid.addRequested.connect(self.addRequested)

        # Add grids as tabs
        self.tabs.addTab(self.background_grid, get_icon("background"), "")
        self.tabs.setTabToolTip(0, "Arrière-plans")
        self.tabs.addTab(self.objects_grid, get_icon("objets"), "")
        self.tabs.setTabToolTip(1, "Objets")
        self.tabs.addTab(self.puppets_grid, get_icon("puppet"), "")
        self.tabs.setTabToolTip(2, "Pantins")

        layout.addWidget(self.tabs)
        self.reload()

    def reload(self) -> None:
        """Populate grids with available assets from the filesystem."""
        self.background_grid.clear()
        self.objects_grid.clear()
        self.puppets_grid.clear()

        asset_dirs = {
            "background": (
                self.background_grid,
                self.root_dir / "assets" / "background",
                {".png", ".jpg", ".jpeg"},
            ),
            "object": (
                self.objects_grid,
                self.root_dir / "assets" / "objets",
                {".png", ".svg"},
            ),
            "puppet": (
                self.puppets_grid,
                self.root_dir / "assets" / "pantins",
                {".svg"},
            ),
        }

        for kind, (grid, path, exts) in asset_dirs.items():
            if not path.exists():
                continue

            files = sorted(
                [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in exts]
            )
            for f in files:
                item = QListWidgetItem(f.name)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(
                    Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
                )

                payload = {"kind": kind, "path": str(f)}
                item.setData(Qt.UserRole, payload)

                try:
                    item.setIcon(QIcon(str(f)))
                except OSError as e:
                    logging.debug("Failed to load icon for '%s': %s", f, e)

                item.setToolTip(str(f))
                grid.addItem(item)
