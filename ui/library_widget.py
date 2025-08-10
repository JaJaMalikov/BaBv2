import os
import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QMimeData, QByteArray, Signal, QPoint, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QMenu
from PySide6.QtGui import QDrag, QIcon


LIB_MIME = "application/x-bab-item"


class _DraggableTree(QTreeWidget):
    addRequested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeWidget.DragOnly)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_context_menu)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return
        payload = item.data(0, Qt.UserRole)
        if not payload:
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(LIB_MIME, QByteArray(json.dumps(payload).encode("utf-8")))
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)

    def _open_context_menu(self, pos: QPoint):
        item = self.itemAt(pos)
        if not item:
            return
        payload = item.data(0, Qt.UserRole)
        if not payload:
            return
        menu = QMenu(self)
        act_add = menu.addAction("Ajouter à la scène")
        action = menu.exec(self.viewport().mapToGlobal(pos))
        if action == act_add:
            self.addRequested.emit(payload)


class LibraryWidget(QWidget):
    addRequested = Signal(dict)

    def __init__(self, root_dir: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.root_dir = Path(root_dir or ".").resolve()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        self.tree = _DraggableTree(self)
        self.tree.addRequested.connect(self.addRequested)
        self.tree.setIconSize(QSize(48, 48))
        lay.addWidget(self.tree)
        self.reload()

    def reload(self):
        self.tree.clear()
        # Define categories
        categories = [
            ("Arrière-plans", self.root_dir / "assets" / "background", {"exts": {".png", ".jpg", ".jpeg"}, "kind": "background"}),
            ("Objets", self.root_dir / "assets" / "objets", {"exts": {".png", ".svg"}, "kind": "object"}),
            ("Pantins", self.root_dir / "assets" / "pantins", {"exts": {".svg"}, "kind": "puppet"}),
        ]

        for title, path, spec in categories:
            parent_item = QTreeWidgetItem([title])
            parent_item.setFlags(Qt.ItemIsEnabled)
            self.tree.addTopLevelItem(parent_item)
            if not path.exists():
                hint = QTreeWidgetItem([f"(dossier manquant: {path})"]) 
                hint.setFlags(Qt.ItemIsEnabled)
                parent_item.addChild(hint)
                continue
            files = sorted([p for p in path.iterdir() if p.is_file() and p.suffix.lower() in spec["exts"]])
            if not files:
                empty = QTreeWidgetItem(["(vide)"])
                empty.setFlags(Qt.ItemIsEnabled)
                parent_item.addChild(empty)
                continue
            for f in files:
                item = QTreeWidgetItem([f.name])
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
                payload = {"kind": spec["kind"], "path": str(f)}
                item.setData(0, Qt.UserRole, payload)
                # Thumbnail/icon
                try:
                    item.setIcon(0, QIcon(str(f)))
                except Exception:
                    pass
                item.setToolTip(0, str(f))
                parent_item.addChild(item)
        self.tree.expandAll()
