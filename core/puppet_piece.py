"""Graphical QGraphicsItems representing puppet pieces and handles."""

from typing import Optional, Tuple, List, Any
import logging
import math

from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsSceneMouseEvent,
    QGraphicsItem,
)
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QTransform
from PySide6.QtSvg import QSvgRenderer  # Added for type hinting

# --- Constantes ---
PIVOT_KEYWORDS = ["coude", "genou", "hanche", "epaule", "cheville", "poignet", "cou"]
HANDLE_Z_VALUE = 1000
PIVOT_Z_VALUE = 999


class RotationHandle(QGraphicsEllipseItem):
    """Circular handle used to rotate a ``PuppetPiece`` around its pivot."""

    def __init__(self, piece: "PuppetPiece") -> None:
        """Create a rotation handle bound to ``piece``."""
        super().__init__(-10, -10, 20, 20)
        self.piece: "PuppetPiece" = piece
        self.setBrush(QBrush(Qt.transparent))
        self.setPen(QPen(Qt.transparent))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setZValue(HANDLE_Z_VALUE)
        self.start_angle: float = 0.0
        self.start_rotation: float = 0.0

    # pylint: disable=invalid-name
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Record starting angle and rotation when interaction begins."""
        pivot_in_scene: QPointF = self.piece.mapToScene(
            self.piece.transformOriginPoint()
        )
        mouse_in_scene: QPointF = event.scenePos()
        vector: QPointF = mouse_in_scene - pivot_in_scene
        self.start_angle = math.degrees(math.atan2(vector.y(), vector.x()))
        self.start_rotation = self.piece.local_rotation
        super().mousePressEvent(event)

    # pylint: disable=invalid-name
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Rotate the bound piece based on mouse movement."""
        pivot_in_scene: QPointF = self.piece.mapToScene(
            self.piece.transformOriginPoint()
        )
        mouse_in_scene: QPointF = event.scenePos()
        vector: QPointF = mouse_in_scene - pivot_in_scene
        current_angle: float = math.degrees(math.atan2(vector.y(), vector.x()))
        delta: float = current_angle - self.start_angle
        self.piece.rotate_piece(self.start_rotation + delta)

    # pylint: disable=invalid-name
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Reset temporary rotation state after interaction."""
        self.start_angle = 0.0
        self.start_rotation = 0.0
        super().mouseReleaseEvent(event)


# pylint: disable=R0903
class PivotHandle(QGraphicsEllipseItem):
    """Small circle visualizing the pivot point of a ``PuppetPiece``."""

    def __init__(self) -> None:
        """Construct a pivot handle with transparent styling."""
        super().__init__(-5, -5, 10, 10)
        self.setBrush(QBrush(Qt.transparent))
        self.setPen(QPen(Qt.transparent))
        self.setZValue(PIVOT_Z_VALUE)


# pylint: disable=R0902
class PuppetPiece(QGraphicsSvgItem):
    """Graphical item representing a puppet member (SVG group).

    The item stores its local rotation (relative to parent) and knows how to
    update its position/rotation from the parent using precomputed relative
    offsets (rel_to_parent). It also owns optional rotation/pivot handles.
    """

    # pylint: disable=R0913, R0917
    def __init__(
        self,
        svg_path: str,
        name: str,
        pivot_x: float = 0.0,
        pivot_y: float = 0.0,
        renderer: Optional[QSvgRenderer] = None,
    ) -> None:
        """Initialize the SVG item with pivot information and optional renderer."""
        if renderer is not None:
            super().__init__()
            self.setSharedRenderer(renderer)
            self.setElementId(name)
        else:
            super().__init__(svg_path)
            self.setElementId(name)

        self.name: str = name
        self.pivot_x: float = pivot_x
        self.pivot_y: float = pivot_y
        self.setTransformOriginPoint(self.pivot_x, self.pivot_y)

        self.parent_piece: Optional["PuppetPiece"] = None
        self.children: List["PuppetPiece"] = []
        self.rel_to_parent: Tuple[float, float] = (0.0, 0.0)
        self.local_rotation: float = 0.0

        # No external geometry listeners (rolled back)

        if "_droite" in name:
            self.handle_color: QColor = QColor(255, 70, 70, 150)
        elif "_gauche" in name:
            self.handle_color: QColor = QColor(70, 255, 70, 150)
        else:
            self.handle_color: QColor = QColor(255, 200, 70, 150)

        self.pivot_handle: PivotHandle = PivotHandle()
        if not any(keyword in name for keyword in PIVOT_KEYWORDS):
            self.rotation_handle: Optional[RotationHandle] = RotationHandle(self)
            brect = self.boundingRect()
            if self.name == "torse":
                self.handle_local_pos = QPointF(
                    brect.center().x(),
                    brect.center().y() - 40,
                )
            else:
                self.handle_local_pos = brect.center()
        else:
            self.rotation_handle = None
            # Initialize if no rotation handle
            self.handle_local_pos: Optional[QPointF] = None

    def set_handle_visibility(self, visible: bool) -> None:
        """Show or hide pivot and rotation handles with themed styling."""
        pen_color: QColor = QColor(255, 255, 255, 180)
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

    def update_handle_positions(self) -> None:
        """Update scene positions of the pivot and rotation handles."""
        pivot_pos: QPointF = self.mapToScene(self.pivot_x, self.pivot_y)
        self.pivot_handle.setPos(pivot_pos)
        if self.rotation_handle and self.handle_local_pos:
            handle_pos: QPointF = self.mapToScene(self.handle_local_pos)
            self.rotation_handle.setPos(handle_pos)
        for child in self.children:
            child.update_handle_positions()

    # pylint: disable=invalid-name
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """Propagate transform updates and handle positions when item changes."""
        if change in (
            QGraphicsItem.ItemPositionHasChanged,
            QGraphicsItem.ItemRotationHasChanged,
            QGraphicsItem.ItemScaleHasChanged,
        ):
            self.update_handle_positions()
            for child in self.children:
                child.update_transform_from_parent()
        return super().itemChange(change, value)

    def set_parent_piece(
        self,
        parent: "PuppetPiece",
        rel_x: float = 0.0,
        rel_y: float = 0.0,
    ) -> None:
        """Define parent piece and relative offset in parent's local space."""
        self.parent_piece = parent
        self.rel_to_parent = (rel_x, rel_y)
        if parent and self not in parent.children:
            parent.children.append(self)

    def update_transform_from_parent(self) -> None:
        """Recompute world transform from parent rotation and stored offset."""
        if not self.parent_piece:
            return

        parent: "PuppetPiece" = self.parent_piece
        parent_rotation: float = parent.rotation()
        dx, dy = self.rel_to_parent
        transform: QTransform = QTransform()
        transform.rotate(parent_rotation)
        transform.translate(dx, dy)
        offset: QPointF = transform.map(QPointF(0.0, 0.0))
        parent_pivot: QPointF = parent.mapToScene(parent.transformOriginPoint())
        scene_pos: QPointF = parent_pivot + offset - QPointF(self.pivot_x, self.pivot_y)
        self.setPos(scene_pos)
        self.setRotation(parent_rotation + self.local_rotation)
        self.update_handle_positions()
        for child in self.children:
            child.update_transform_from_parent()

    def rotate_piece(self, angle_degrees: float) -> None:
        """Set local rotation and propagate transform updates to children."""
        self.local_rotation = angle_degrees
        if self.parent_piece:
            self.update_transform_from_parent()
        else:
            self.setRotation(self.local_rotation)
            self.update_handle_positions()
        for child in self.children:
            child.update_transform_from_parent()

    # Deselect objects when starting to interact with a puppet piece to avoid accidental moves
    # pylint: disable=invalid-name
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Ensure only puppet pieces remain selected when manipulating handles."""
        try:
            if not event.modifiers() & (Qt.ShiftModifier | Qt.ControlModifier):
                sc = self.scene()
                if sc is not None:
                    for it in list(sc.selectedItems()):
                        # Keep selection on puppet pieces; clear for other items (objects)
                        if not isinstance(it, PuppetPiece):
                            it.setSelected(False)
        except (RuntimeError, AttributeError):
            logging.exception("Failed to sanitize selection in mousePressEvent")
        super().mousePressEvent(event)
