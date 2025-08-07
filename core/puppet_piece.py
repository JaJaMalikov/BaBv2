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
        parent_rotation = self.parent.parent_piece.rotation() if self.parent.parent_piece else 0
        self.parent.rotate_piece(angle_in_scene - parent_rotation)


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

        # Chaînage logique sans dépendre de QGraphicsItem
        self.parent_piece = None
        self.children = []
        self.rel_to_parent = (0.0, 0.0)
        self.local_rotation = 0.0

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
        # Propagation du déplacement aux enfants
        if change == QGraphicsItem.ItemPositionHasChanged:
            for child in self.children:
                child.update_transform_from_parent()
        return super().itemChange(change, value)

    def set_parent_piece(self, parent, rel_x=0.0, rel_y=0.0):
        self.parent_piece = parent
        self.rel_to_parent = (rel_x, rel_y)
        if parent and self not in parent.children:
            parent.children.append(self)

    def update_transform_from_parent(self):
        if not self.parent_piece:
            return

        parent = self.parent_piece
        parent_rotation = parent.rotation()
        angle_rad = math.radians(parent_rotation)
        dx, dy = self.rel_to_parent
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        rotated_dx = dx * cos_a - dy * sin_a
        rotated_dy = dx * sin_a + dy * cos_a
        parent_pivot = parent.mapToScene(parent.transformOriginPoint())
        scene_x = parent_pivot.x() + rotated_dx
        scene_y = parent_pivot.y() + rotated_dy
        self.setPos(scene_x - self.pivot_x, scene_y - self.pivot_y)
        self.setRotation(parent_rotation + self.local_rotation)
        for child in self.children:
            child.update_transform_from_parent()

    def rotate_piece(self, angle_degrees):
        self.local_rotation = angle_degrees
        if self.parent_piece:
            self.update_transform_from_parent()
        else:
            self.setRotation(self.local_rotation)
            for child in self.children:
                child.update_transform_from_parent()
