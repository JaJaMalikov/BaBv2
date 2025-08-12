import logging
import json
from PySide6.QtWidgets import (
    QGraphicsView,
    QWidget,
    QHBoxLayout,
    QToolButton,
    QGraphicsScene, # Added
)
from PySide6.QtGui import QIcon, QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent, QWheelEvent, QAction
from PySide6.QtCore import Qt, Signal, QPointF, QSize, QEvent

from ui.draggable_widget import DraggableOverlay
from ui.icons import (
    icon_plus, icon_minus, icon_fit, icon_rotate, icon_onion,
    icon_open_menu, icon_close_menu, icon_close_menu_inv
)
from ui.library_widget import LIB_MIME


from typing import Optional, Any, Callable, Dict, List

class ZoomableView(QGraphicsView):
    zoom_requested = Signal(float)
    fit_requested = Signal()
    handles_toggled = Signal(bool)
    onion_toggled = Signal(bool)
    item_dropped = Signal(dict, QPointF)

    def __init__(self, scene: QGraphicsScene, parent: Optional[QWidget] = None) -> None:
        super().__init__(scene, parent)
        self._overlay: Optional[DraggableOverlay] = None
        self._did_initial_fit: bool = False
        self._build_overlay()
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)

    def _build_overlay(self) -> None:
        self._overlay = DraggableOverlay(self)

        self.layout: QHBoxLayout = QHBoxLayout(self._overlay)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(2)

        icon_size: int = 32
        button_size: int = 36

        def make_btn(icon: Optional[QIcon], tooltip: str, cb: Optional[Callable[[], None]] = None, checkable: bool = False) -> QToolButton:
            btn: QToolButton = QToolButton(self._overlay)
            if icon:
                btn.setIcon(icon)
                btn.setIconSize(QSize(icon_size, icon_size))
            btn.setToolTip(tooltip)
            if cb: btn.clicked.connect(cb)
            btn.setCheckable(checkable)
            btn.setFixedSize(button_size, button_size)
            btn.setAutoRaise(True)
            return btn

        self.collapse_btn: QToolButton = make_btn(icon_close_menu(), "Replier/Déplier le panneau", checkable=True)
        self.collapse_btn.setChecked(True)
        self.collapse_btn.toggled.connect(self.toggle_overlay_collapse)
        self.layout.addWidget(self.collapse_btn)

        self.zoom_out_btn: QToolButton = make_btn(icon_minus(), "Zoom arrière (Ctrl+Molette)", lambda: self.zoom_requested.emit(0.8))
        self.zoom_in_btn: QToolButton = make_btn(icon_plus(), "Zoom avant (Ctrl+Molette)", lambda: self.zoom_requested.emit(1.25))
        self.fit_btn: QToolButton = make_btn(icon_fit(), "Ajuster à la vue", self.fit_requested.emit)
        
        self.handles_btn: QToolButton = make_btn(icon_rotate(), "Afficher/Masquer les poignées", checkable=True)
        self.handles_btn.toggled.connect(self.handles_toggled)

        self.onion_btn: QToolButton = make_btn(icon_onion(), "Onion skin (fantômes)", checkable=True)
        self.onion_btn.toggled.connect(self.onion_toggled)

        self.tool_widgets: List[QWidget] = [self.zoom_out_btn, self.zoom_in_btn, self.fit_btn, self.handles_btn, self.onion_btn]
        for w in self.tool_widgets:
            self.layout.addWidget(w)

        self._overlay.move(10, 10)

    def _build_main_tools_overlay(self, main_window: QWidget) -> None:
        self._main_tools_overlay = DraggableOverlay(self)

        self.main_tools_layout: QHBoxLayout = QHBoxLayout(self._main_tools_overlay)
        self.main_tools_layout.setContentsMargins(4, 4, 4, 4)
        self.main_tools_layout.setSpacing(2)

        icon_size: int = 32
        button_size: int = 36

        def make_btn(action: QAction, checkable: bool = False) -> QToolButton:
            btn: QToolButton = QToolButton(self._main_tools_overlay)
            btn.setDefaultAction(action)
            btn.setIconSize(QSize(icon_size, icon_size))
            btn.setCheckable(checkable)
            btn.setFixedSize(button_size, button_size)
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setAutoRaise(True)
            return btn

        self.main_collapse_btn: QToolButton = QToolButton(self._main_tools_overlay)
        self.main_collapse_btn.setIcon(icon_close_menu_inv())
        self.main_collapse_btn.setIconSize(QSize(icon_size, icon_size))
        self.main_collapse_btn.setCheckable(True)
        self.main_collapse_btn.setChecked(True)
        self.main_collapse_btn.setFixedSize(button_size, button_size)
        self.main_collapse_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.main_collapse_btn.setAutoRaise(True)
        self.main_collapse_btn.toggled.connect(self.toggle_main_tools_collapse)

        save_btn: QToolButton = make_btn(main_window.save_action)
        load_btn: QToolButton = make_btn(main_window.load_action)
        scene_size_btn: QToolButton = make_btn(main_window.scene_size_action)
        background_btn: QToolButton = make_btn(main_window.background_action)

        library_toggle_btn: QToolButton = make_btn(main_window.toggle_library_action, checkable=True)
        inspector_toggle_btn: QToolButton = make_btn(main_window.toggle_inspector_action, checkable=True)
        timeline_toggle_btn: QToolButton = make_btn(main_window.timeline_dock.toggleViewAction(), checkable=True)

        library_toggle_btn.setChecked(main_window.library_overlay.isVisible())
        inspector_toggle_btn.setChecked(main_window.inspector_overlay.isVisible())
        timeline_toggle_btn.setChecked(main_window.timeline_dock.isVisible())

        self.main_tool_buttons: List[QToolButton] = [
            save_btn,
            load_btn,
            scene_size_btn,
            background_btn,
            library_toggle_btn,
            inspector_toggle_btn,
            timeline_toggle_btn,
        ]

        self.main_tools_layout.addStretch()
        for w in self.main_tool_buttons:
            self.main_tools_layout.addWidget(w)
        self.main_tools_layout.addWidget(self.main_collapse_btn)

        self._main_tools_overlay.move(10, 60)

    def toggle_overlay_collapse(self, checked: bool) -> None:
        icon: QIcon = icon_close_menu() if checked else icon_open_menu()
        self.collapse_btn.setIcon(icon)
        for w in self.tool_widgets:
            w.setVisible(checked)
        self._overlay.adjustSize()

    def toggle_main_tools_collapse(self, checked: bool) -> None:
        icon: QIcon = icon_close_menu_inv() if checked else icon_open_menu()
        self.main_collapse_btn.setIcon(icon)

        overlay = getattr(self, "_main_tools_overlay", None)
        if not overlay:
            return

        # Store the position of the right edge before resizing
        old_right_x = overlay.geometry().right()

        # Hide/show the tool buttons
        for w in getattr(self, "main_tool_buttons", []):
            w.setVisible(checked)

        # Adjust the overlay's size to fit the new content
        overlay.adjustSize()

        # Calculate the new top-left x-position to keep the right edge stationary
        new_x = old_right_x - overlay.width()

        # Move the overlay to the new position
        overlay.move(new_x, overlay.y())

    # Removed zoom label (cleaner overlay)

    def resizeEvent(self, event: QEvent) -> None:
        super().resizeEvent(event)
        if not self._did_initial_fit and self.width() > 0 and self.height() > 0:
            self._did_initial_fit = True
            self.fit_requested.emit()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() == Qt.ControlModifier:
            factor: float = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
            self.zoom_requested.emit(factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MiddleButton:
            self._panning: bool = True
            self._pan_start: QPointF = event.position()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if getattr(self, "_panning", False):
            delta: QPointF = event.position() - self._pan_start
            self._pan_start = event.position()
            h, v = self.horizontalScrollBar(), self.verticalScrollBar()
            h.setValue(h.value() - int(delta.x()))
            v.setValue(v.value() - int(delta.y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MiddleButton and getattr(self, "_panning", False):
            self._panning = False
            self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(LIB_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(LIB_MIME):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasFormat(LIB_MIME):
            try:
                data: bytes = bytes(event.mimeData().data(LIB_MIME))
                payload: Dict[str, Any] = json.loads(data.decode('utf-8'))
                self.item_dropped.emit(payload, event.position())
            except Exception as e:
                logging.error(f"Drop failed: {e}")
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
