import math

from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsSceneMouseEvent, QGraphicsItem
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor

# --- Constantes ---
PIVOT_KEYWORDS = ["coude", "genou", "hanche", "epaule", "cheville", "poignet", "cou"]
HANDLE_Z_VALUE = 1000
PIVOT_Z_VALUE = 999

class RotationHandle(QGraphicsEllipseItem):
    def __init__(self, piece):
        super().__init__(-10, -10, 20, 20)
        self.piece = piece
        self.setBrush(QBrush(Qt.transparent))
        self.setPen(QPen(Qt.transparent))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setZValue(HANDLE_Z_VALUE)
        self.start_angle = 0
        self.start_rotation = 0

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        pivot_in_scene = self.piece.mapToScene(self.piece.transformOriginPoint())
        mouse_in_scene = event.scenePos()
        vector = mouse_in_scene - pivot_in_scene
        self.start_angle = math.degrees(math.atan2(vector.y(), vector.x()))
        self.start_rotation = self.piece.local_rotation
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        pivot_in_scene = self.piece.mapToScene(self.piece.transformOriginPoint())
        mouse_in_scene = event.scenePos()
        vector = mouse_in_scene - pivot_in_scene
        current_angle = math.degrees(math.atan2(vector.y(), vector.x()))
        delta = current_angle - self.start_angle
        self.piece.rotate_piece(self.start_rotation + delta)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        self.start_angle = 0
        self.start_rotation = 0
        super().mouseReleaseEvent(event)

class PivotHandle(QGraphicsEllipseItem):
    def __init__(self):
        super().__init__(-5, -5, 10, 10)
        self.setBrush(QBrush(Qt.transparent))
        self.setPen(QPen(Qt.transparent))
        self.setZValue(PIVOT_Z_VALUE)

class PuppetPiece(QGraphicsSvgItem):
    def __init__(
        self,
        svg_path: str,
        name: str,
        pivot_x: float = 0.0,
        pivot_y: float = 0.0,
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
        self.grid = grid
        self.setTransformOriginPoint(self.pivot_x, self.pivot_y)

        self.parent_piece = None
        self.children = []
        self.rel_to_parent = (0.0, 0.0)
        self.local_rotation = 0.0

        if "_droite" in name:
            self.handle_color = QColor(255, 70, 70, 150)
        elif "_gauche" in name:
            self.handle_color = QColor(70, 255, 70, 150)
        else:
            self.handle_color = QColor(255, 200, 70, 150)

        self.pivot_handle = PivotHandle()
        if not any(keyword in name for keyword in PIVOT_KEYWORDS):
            self.rotation_handle = RotationHandle(self)
            brect = self.boundingRect()
            if self.name == "torse":
                self.handle_local_pos = QPointF(brect.center().x(), brect.center().y() - 40)
            else:
                self.handle_local_pos = brect.center()
        else:
            self.rotation_handle = None

    def set_handle_visibility(self, visible):
        pen_color = QColor(255, 255, 255, 180)
        if visible:
            self.pivot_handle.setBrush(QBrush(QColor(70, 200, 255, 180)))
            self.pivot_handle.setPen(QPen(pen_color, 1))
        else:
            self.pivot_handle.setBrush(QBrush(Qt.transparent))
            self.pivot_handle.setPen(QPen(Qt.transparent))

        if self.rotation_handle:
            if visible:
                self.rotation_handle.setBrush(QBrush(self.handle_color))
                self.rotation_handle.setPen(QPen(pen_color, 1.5))
            else:
                self.rotation_handle.setBrush(QBrush(Qt.transparent))
                self.rotation_handle.setPen(QPen(Qt.transparent))

    def update_handle_positions(self):
        pivot_pos = self.mapToScene(self.pivot_x, self.pivot_y)
        self.pivot_handle.setPos(pivot_pos)
        if self.rotation_handle:
            handle_pos = self.mapToScene(self.handle_local_pos)
            self.rotation_handle.setPos(handle_pos)
        for child in self.children:
            child.update_handle_positions()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene() and self.grid:
            return self.grid.snap_to_grid(value)
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.update_handle_positions()
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
        self.update_handle_positions()
        for child in self.children:
            child.update_transform_from_parent()

    def rotate_piece(self, angle_degrees):
        self.local_rotation = angle_degrees
        if self.parent_piece:
            self.update_transform_from_parent()
        else:
            self.setRotation(self.local_rotation)
            self.update_handle_positions()
        for child in self.children:
            child.update_transform_from_parent()
