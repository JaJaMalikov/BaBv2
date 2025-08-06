import math

from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsSceneMouseEvent, QGraphicsItem
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QPen


class RotationHandle(QGraphicsEllipseItem):
    def __init__(self, parent):
        super().__init__(-10, -10, 20, 20)
        self.setParentItem(parent)
        self.parent = parent
        self.setBrush(QBrush(Qt.transparent))
        self.setPen(QPen(Qt.transparent))
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if not self.parent:
            return
        pivot_in_scene = self.parent.mapToScene(self.parent.transformOriginPoint())
        mouse_in_scene = event.scenePos()
        vector = mouse_in_scene - pivot_in_scene
        angle_in_scene = math.degrees(math.atan2(vector.y(), vector.x()))
        parent_rotation = self.parent.parentItem().rotation() if self.parent.parentItem() else 0
        self.parent.setRotation(angle_in_scene - parent_rotation)


class PuppetPiece(QGraphicsSvgItem):
    def __init__(
        self,
        svg_path: str,
        name: str,
        pivot_x: float = 0.0,
        pivot_y: float = 0.0,
        target_pivot_x: float = None,
        target_pivot_y: float = None,
        renderer=None,
        grid=None
    ):
        if renderer is not None:
            super().__init__()
            self.setSharedRenderer(renderer)
            self.setElementId(name)
        else:
            super().__init__(svg_path)
            self.setElementId(name)

        self.name = name
        self.pivot_x = float(pivot_x)
        self.pivot_y = float(pivot_y)
        self.target_pivot_x = float(target_pivot_x) if target_pivot_x is not None else None
        self.target_pivot_y = float(target_pivot_y) if target_pivot_y is not None else None
        self.grid = grid
        self.setTransformOriginPoint(self.pivot_x, self.pivot_y)

        # Handle aligné dans l'axe du segment
        if name not in ["main_droite", "main_gauche"]:
            self.rotation_handle = RotationHandle(self)
            if self.target_pivot_x is not None and self.target_pivot_y is not None:
                dx = self.target_pivot_x - self.pivot_x
                dy = self.target_pivot_y - self.pivot_y
                norm = (dx ** 2 + dy ** 2) ** 0.5 or 1
                offset = 30  # distance (pixels) du pivot
                handle_x = self.pivot_x + dx / norm * offset
                handle_y = self.pivot_y + dy / norm * offset
            else:
                handle_x = self.pivot_x + 30
                handle_y = self.pivot_y
            self.rotation_handle.setPos(handle_x, handle_y)
        else:
            self.rotation_handle = None

    def itemChange(self, change, value):
        # Magnétisme à la grille
        if change == QGraphicsItem.ItemPositionChange and self.scene() and self.grid:
            return self.grid.snap_to_grid(value)
        # Z-value du handle quand l'item change de Z
        if change == QGraphicsItem.ItemZValueHasChanged and self.rotation_handle:
            self.rotation_handle.setZValue(value + 1)
        # Z-value du handle quand la pièce est ajoutée à la scène
        if change == QGraphicsItem.ItemSceneHasChanged and self.rotation_handle:
            self.rotation_handle.setZValue(self.zValue() + 1)
        return super().itemChange(change, value)

    def rotate_piece(self, angle_degrees):
        self.setRotation(angle_degrees)
