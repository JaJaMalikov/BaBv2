import json
from PySide6.QtWidgets import (
    QGraphicsView,
    QWidget,
    QHBoxLayout,
    QToolButton,
    QLabel,
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, Signal, QPointF, QSize, QTimer

from ui.draggable_widget import DraggableOverlay
from ui.icons import (
    icon_plus, icon_minus, icon_fit, icon_rotate,
    icon_chevron_left, icon_chevron_right
)
from ui.styles import BUTTON_STYLE
from ui.library_widget import LIB_MIME


class ZoomableView(QGraphicsView):
    zoom_requested = Signal(float)
    fit_requested = Signal()
    handles_toggled = Signal(bool)
    item_dropped = Signal(dict, QPointF)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._overlay = None
        self._build_overlay()
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.fit_requested.emit)

    def _build_overlay(self):
        self._overlay = DraggableOverlay(self)

        self.layout = QHBoxLayout(self._overlay)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(2)

        icon_size = 32
        button_size = 36

        def make_btn(icon: QIcon | None, tooltip, cb=None, checkable=False):
            btn = QToolButton(self._overlay)
            if icon:
                btn.setIcon(icon)
                btn.setIconSize(QSize(icon_size, icon_size))
            btn.setToolTip(tooltip)
            if cb: btn.clicked.connect(cb)
            btn.setCheckable(checkable)
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setFixedSize(button_size, button_size)
            btn.setAutoRaise(True)
            return btn

        self.collapse_btn = make_btn(icon_chevron_left(), "Replier/Déplier le panneau", checkable=True)
        self.collapse_btn.setChecked(True)
        self.collapse_btn.toggled.connect(self.toggle_overlay_collapse)
        self.layout.addWidget(self.collapse_btn)

        self.zoom_out_btn = make_btn(icon_minus(), "Zoom arrière (Ctrl+Molette)", lambda: self.zoom_requested.emit(0.8))
        self.zoom_in_btn = make_btn(icon_plus(), "Zoom avant (Ctrl+Molette)", lambda: self.zoom_requested.emit(1.25))
        self.fit_btn = make_btn(icon_fit(), "Ajuster à la vue", self.fit_requested.emit)
        
        self.handles_btn = make_btn(icon_rotate(), "Afficher/Masquer les poignées", checkable=True)
        self.handles_btn.toggled.connect(self.handles_toggled)

        self._zoom_label = QLabel("100%", self._overlay)
        self._zoom_label.setStyleSheet("color: #CFCFCF; padding: 2px 4px;")

        self.tool_widgets = [self.zoom_out_btn, self.zoom_in_btn, self.fit_btn, self.handles_btn, self._zoom_label]
        for w in self.tool_widgets:
            self.layout.addWidget(w)

        self._overlay.move(10, 10)

    def build_main_tools_overlay(
        self,
        save_action,
        load_action,
        scene_size_action,
        background_action,
        library_dock,
        inspector_dock,
        timeline_dock,
    ):
        self._main_tools_overlay = DraggableOverlay(self)

        layout = QHBoxLayout(self._main_tools_overlay)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        icon_size = 32
        button_size = 36

        def make_btn(action, checkable=False):
            btn = QToolButton(self._main_tools_overlay)
            btn.setDefaultAction(action)
            btn.setIconSize(QSize(icon_size, icon_size))
            btn.setCheckable(checkable)
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setFixedSize(button_size, button_size)
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setAutoRaise(True)
            return btn

        collapse_btn = make_btn(QAction(icon_chevron_left(), "Replier/Déplier", self), checkable=True)
        collapse_btn.setChecked(True)

        save_btn = make_btn(save_action)
        load_btn = make_btn(load_action)
        scene_size_btn = make_btn(scene_size_action)
        background_btn = make_btn(background_action)

        library_toggle_btn = make_btn(library_dock.toggleViewAction(), checkable=True)
        inspector_toggle_btn = make_btn(inspector_dock.toggleViewAction(), checkable=True)
        timeline_toggle_btn = make_btn(timeline_dock.toggleViewAction(), checkable=True)

        library_toggle_btn.setChecked(library_dock.isVisible())
        inspector_toggle_btn.setChecked(inspector_dock.isVisible())
        timeline_toggle_btn.setChecked(timeline_dock.isVisible())

        library_dock.visibilityChanged.connect(library_toggle_btn.setChecked)
        inspector_dock.visibilityChanged.connect(inspector_toggle_btn.setChecked)
        timeline_dock.visibilityChanged.connect(timeline_toggle_btn.setChecked)

        self._main_tool_buttons = [
            save_btn,
            load_btn,
            scene_size_btn,
            background_btn,
            library_toggle_btn,
            inspector_toggle_btn,
            timeline_toggle_btn,
        ]

        def toggle_main_collapse(checked):
            icon = icon_chevron_left() if checked else icon_chevron_right()
            collapse_btn.setIcon(icon)
            for w in self._main_tool_buttons:
                w.setVisible(checked)
            self._main_tools_overlay.adjustSize()

        collapse_btn.toggled.connect(toggle_main_collapse)

        layout.addWidget(collapse_btn)
        for w in self._main_tool_buttons:
            layout.addWidget(w)

        self._main_tools_overlay.move(10, 60)

    def toggle_overlay_collapse(self, checked):
        icon = icon_chevron_left() if checked else icon_chevron_right()
        self.collapse_btn.setIcon(icon)
        for w in self.tool_widgets:
            w.setVisible(checked)
        self._overlay.adjustSize()

    def set_zoom_label(self, text: str):
        if self._zoom_label: self._zoom_label.setText(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
            self.zoom_requested.emit(factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_panning", False):
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            h, v = self.horizontalScrollBar(), self.verticalScrollBar()
            h.setValue(h.value() - int(delta.x()))
            v.setValue(v.value() - int(delta.y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and getattr(self, "_panning", False):
            self._panning = False
            self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(LIB_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(LIB_MIME):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(LIB_MIME):
            try:
                data = bytes(event.mimeData().data(LIB_MIME)).decode('utf-8')
                payload = json.loads(data)
                self.item_dropped.emit(payload, event.position())
            except Exception as e:
                print(f"Drop failed: {e}")
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
