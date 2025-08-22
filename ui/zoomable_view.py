"""Module for the zoomable view, which provides a user interface for zooming and panning the scene."""

import json
import logging
from typing import Any, Dict, List, Optional

from PySide6.QtCore import (
    QEvent,
    QPointF,
    QSettings,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QMouseEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QToolButton,
    QWidget,
)

from ui.draggable_widget import DraggableOverlay
from ui.icons import (
    icon_close_menu,
    icon_close_menu_inv,
    icon_fit,
    icon_minus,
    icon_onion,
    icon_open_menu,
    icon_plus,
    icon_rotate,
)
from ui.views.library.library_widget import LIB_MIME
from ui.utils import make_tool_button
from ui.settings_keys import (
    ORG,
    APP,
    UI_ICON_SIZE,
    UI_MENU_ORDER,
    UI_MENU_VIS,
    UI_MENU_CUSTOM_VISIBLE,
    UI_DEFAULT_CUSTOM_SIZE,
    UI_DEFAULT_CUSTOM_POS,
    MAIN_MENU,
    QUICK_MENU,
    CUSTOM_MENU,
)


class ZoomableView(QGraphicsView):
    """A QGraphicsView that supports zooming, panning, and overlay widgets."""

    zoom_requested = Signal(float)
    fit_requested = Signal()
    handles_toggled = Signal(bool)
    onion_toggled = Signal(bool)
    item_dropped = Signal(dict, QPointF)

    def __init__(self, scene: QGraphicsScene, parent: Optional[QWidget] = None) -> None:
        """
        Initializes the ZoomableView.

        Args:
            scene: The QGraphicsScene to display.
            parent: The parent widget.
        """
        super().__init__(scene, parent)
        self._overlay: Optional[DraggableOverlay] = None
        self._did_initial_fit: bool = False
        self._build_overlay()
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)

    def _build_overlay(self) -> None:
        """Builds the overlay widget with tool buttons."""
        self._overlay = DraggableOverlay(self)

        self.layout: QHBoxLayout = QHBoxLayout(self._overlay)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(2)
        s = QSettings(ORG, APP)
        try:
            from ui.ui_profile import _int as _to_int
        except Exception:
            _to_int = lambda v, d=32: int(v) if v is not None else d  # type: ignore
        size_val = _to_int(s.value(UI_ICON_SIZE), 32)
        icon_size: int = max(16, min(128, int(size_val)))
        button_size: int = max(28, icon_size + 4)

        self.collapse_btn: QToolButton = make_tool_button(
            self._overlay,
            icon=icon_close_menu(),
            tooltip="Replier/Déplier le panneau",
            checkable=True,
            icon_size=icon_size,
            button_size=button_size,
        )
        self.collapse_btn.setChecked(True)
        self.collapse_btn.toggled.connect(self.toggle_overlay_collapse)
        self.layout.addWidget(self.collapse_btn)

        self.zoom_out_btn: QToolButton = make_tool_button(
            self._overlay,
            icon=icon_minus(),
            tooltip="Zoom arrière (Ctrl+Molette)",
            callback=lambda: self.zoom_requested.emit(0.8),
            icon_size=icon_size,
            button_size=button_size,
        )
        self.zoom_in_btn: QToolButton = make_tool_button(
            self._overlay,
            icon=icon_plus(),
            tooltip="Zoom avant (Ctrl+Molette)",
            callback=lambda: self.zoom_requested.emit(1.25),
            icon_size=icon_size,
            button_size=button_size,
        )
        self.fit_btn: QToolButton = make_tool_button(
            self._overlay,
            icon=icon_fit(),
            tooltip="Ajuster à la vue",
            callback=self.fit_requested.emit,
            icon_size=icon_size,
            button_size=button_size,
        )

        self.handles_btn: QToolButton = make_tool_button(
            self._overlay,
            icon=icon_rotate(),
            tooltip="Afficher/Masquer les poignées",
            checkable=True,
            icon_size=icon_size,
            button_size=button_size,
        )
        self.handles_btn.toggled.connect(self.handles_toggled)

        self.onion_btn: QToolButton = make_tool_button(
            self._overlay,
            icon=icon_onion(),
            tooltip="Onion skin (fantômes)",
            checkable=True,
            icon_size=icon_size,
            button_size=button_size,
        )
        self.onion_btn.toggled.connect(self.onion_toggled)

        self.tool_widgets: List[QWidget] = [
            self.zoom_out_btn,
            self.zoom_in_btn,
            self.fit_btn,
            self.handles_btn,
            self.onion_btn,
        ]
        for w in self.tool_widgets:
            self.layout.addWidget(w)

        self._overlay.move(10, 10)
        self.apply_menu_settings_quick()

    def _build_main_tools_overlay(self, main_window: QWidget) -> None:
        """
        Builds the main tools overlay.

        Args:
            main_window: The main window instance.
        """
        self._main_tools_overlay = DraggableOverlay(self)

        self.main_tools_layout: QHBoxLayout = QHBoxLayout(self._main_tools_overlay)
        self.main_tools_layout.setContentsMargins(4, 4, 4, 4)
        self.main_tools_layout.setSpacing(2)
        s = QSettings(ORG, APP)
        try:
            from ui.ui_profile import _int as _to_int
        except Exception:
            _to_int = lambda v, d=32: int(v) if v is not None else d  # type: ignore
        size_val = _to_int(s.value(UI_ICON_SIZE), 32)
        icon_size: int = max(16, min(128, int(size_val)))
        button_size: int = max(28, icon_size + 4)

        self.main_collapse_btn: QToolButton = make_tool_button(
            self._main_tools_overlay,
            icon=icon_close_menu_inv(),
            checkable=True,
            icon_size=icon_size,
            button_size=button_size,
        )
        self.main_collapse_btn.setChecked(True)
        self.main_collapse_btn.toggled.connect(self.toggle_main_tools_collapse)

        save_btn: QToolButton = make_tool_button(
            self._main_tools_overlay,
            action=main_window.save_action,
            icon_size=icon_size,
            button_size=button_size,
        )
        load_btn: QToolButton = make_tool_button(
            self._main_tools_overlay,
            action=main_window.load_action,
            icon_size=icon_size,
            button_size=button_size,
        )
        scene_size_btn: QToolButton = make_tool_button(
            self._main_tools_overlay,
            action=main_window.scene_size_action,
            icon_size=icon_size,
            button_size=button_size,
        )
        background_btn: QToolButton = make_tool_button(
            self._main_tools_overlay,
            action=main_window.background_action,
            icon_size=icon_size,
            button_size=button_size,
        )
        settings_btn: QToolButton = make_tool_button(
            self._main_tools_overlay,
            action=main_window.settings_action,
            icon_size=icon_size,
            button_size=button_size,
        )
        reset_scene_btn: QToolButton = make_tool_button(
            self._main_tools_overlay,
            action=main_window.reset_scene_action,
            icon_size=icon_size,
            button_size=button_size,
        )
        reset_ui_btn: QToolButton = make_tool_button(
            self._main_tools_overlay,
            action=main_window.reset_ui_action,
            icon_size=icon_size,
            button_size=button_size,
        )

        library_toggle_btn: QToolButton = make_tool_button(
            self._main_tools_overlay,
            action=main_window.toggle_library_action,
            checkable=True,
            icon_size=icon_size,
            button_size=button_size,
        )
        inspector_toggle_btn: QToolButton = make_tool_button(
            self._main_tools_overlay,
            action=main_window.toggle_inspector_action,
            checkable=True,
            icon_size=icon_size,
            button_size=button_size,
        )
        timeline_toggle_btn: QToolButton = make_tool_button(
            self._main_tools_overlay,
            action=main_window.timeline_dock.toggleViewAction(),
            checkable=True,
            icon_size=icon_size,
            button_size=button_size,
        )
        custom_toggle_btn: QToolButton = make_tool_button(
            self._main_tools_overlay,
            action=main_window.toggle_custom_action,
            checkable=True,
            icon_size=icon_size,
            button_size=button_size,
        )

        library_toggle_btn.setChecked(main_window.library_overlay.isVisible())
        inspector_toggle_btn.setChecked(main_window.inspector_overlay.isVisible())
        timeline_toggle_btn.setChecked(main_window.timeline_dock.isVisible())

        # Mapping for visibility/order control
        self.main_tool_buttons_map = {
            "save": save_btn,
            "load": load_btn,
            "scene_size": scene_size_btn,
            "background": background_btn,
            "add_light": make_tool_button(
                self._main_tools_overlay,
                action=main_window.add_light_action,
                icon_size=icon_size,
                button_size=button_size,
            ),
            "settings": settings_btn,
            "reset_scene": reset_scene_btn,
            "reset_ui": reset_ui_btn,
            "toggle_library": library_toggle_btn,
            "toggle_inspector": inspector_toggle_btn,
            "toggle_timeline": timeline_toggle_btn,
            "toggle_custom": custom_toggle_btn,
        }
        self.main_tool_buttons: List[QToolButton] = list(
            self.main_tool_buttons_map.values()
        )

        self.main_tools_layout.addStretch()
        for w in self.main_tool_buttons:
            self.main_tools_layout.addWidget(w)
        self.main_tools_layout.addWidget(self.main_collapse_btn)

        self._main_tools_overlay.move(10, 60)
        self.apply_menu_settings_main()

    def _build_custom_tools_overlay(self, main_window: QWidget) -> None:
        """
        Builds the custom tools overlay.

        Args:
            main_window: The main window instance.
        """
        self._custom_tools_overlay = DraggableOverlay(self)
        lay: QHBoxLayout = QHBoxLayout(self._custom_tools_overlay)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(2)
        s = QSettings(ORG, APP)
        try:
            from ui.ui_profile import _int as _to_int
        except Exception:
            _to_int = lambda v, d=32: int(v) if v is not None else d  # type: ignore
        size_val = _to_int(s.value(UI_ICON_SIZE), 32)
        icon_size: int = max(16, min(128, int(size_val)))
        button_size: int = max(28, icon_size + 4)

        def make_btn(action: QAction, checkable: bool = False) -> QToolButton:
            btn: QToolButton = QToolButton(self._custom_tools_overlay)
            btn.setDefaultAction(action)
            btn.setIconSize(QSize(icon_size, icon_size))
            btn.setCheckable(checkable)
            btn.setFixedSize(button_size, button_size)
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setAutoRaise(True)
            return btn

        # Buttons pool (same as main overlay, excluding toggles that don't make sense?) keep all
        pool = {
            "save": make_btn(main_window.save_action),
            "load": make_btn(main_window.load_action),
            "scene_size": make_btn(main_window.scene_size_action),
            "background": make_btn(main_window.background_action),
            "settings": make_btn(main_window.settings_action),
            "reset_scene": make_btn(main_window.reset_scene_action),
            "reset_ui": make_btn(main_window.reset_ui_action),
            "toggle_library": make_btn(
                main_window.toggle_library_action, checkable=True
            ),
            "toggle_inspector": make_btn(
                main_window.toggle_inspector_action, checkable=True
            ),
            "toggle_timeline": make_btn(
                main_window.timeline_dock.toggleViewAction(), checkable=True
            ),
        }
        from ui.menu_defaults import CUSTOM_DEFAULT_ORDER

        order = s.value(UI_MENU_ORDER(CUSTOM_MENU)) or list(CUSTOM_DEFAULT_ORDER[:5])
        if isinstance(order, str):
            order = [k for k in order.split(",") if k]
        for key in order:
            btn = pool.get(key)
            if not btn:
                continue
            vis = s.value(UI_MENU_VIS(CUSTOM_MENU, key))
            visible = True if vis is None else (vis in [True, "true", "1"]) 
            btn.setVisible(visible)
            lay.addWidget(btn)
        # Geometry defaults
        csize = s.value(UI_DEFAULT_CUSTOM_SIZE)
        cpos = s.value(UI_DEFAULT_CUSTOM_POS)
        cw, ch = 320, 60
        try:
            if csize:
                cw = int(csize.width()) if hasattr(csize, "width") else int(csize[0])
                ch = int(csize.height()) if hasattr(csize, "height") else int(csize[1])
        except (TypeError, ValueError, AttributeError):
            logging.exception("Invalid custom overlay size in settings")
        if cpos and hasattr(cpos, "x"):
            self._custom_tools_overlay.setGeometry(int(cpos.x()), int(cpos.y()), cw, ch)
        else:
            self._custom_tools_overlay.setGeometry(10, 110, cw, ch)
        visible = s.value(UI_MENU_CUSTOM_VISIBLE)
        self._custom_tools_overlay.setVisible(visible in [True, "true", "1"])

    def _set_overlay_collapsed(
        self,
        overlay: Optional[DraggableOverlay],
        buttons: List[QWidget],
        collapse_btn: QToolButton,
        checked: bool,
    ) -> None:
        """
        Shared logic for collapsing overlays.

        Args:
            overlay: The overlay to collapse.
            buttons: The list of buttons in the overlay.
            collapse_btn: The collapse button.
            checked: The checked state of the collapse button.
        """
        if overlay is None:
            return

        # Determine which icon to use for the collapse button
        if collapse_btn is getattr(self, "main_collapse_btn", None):
            collapse_btn.setIcon(icon_close_menu_inv() if checked else icon_open_menu())
        else:
            collapse_btn.setIcon(icon_close_menu() if checked else icon_open_menu())

        # Hide/show the tool buttons. When expanding, respect configured visibility/order.
        if checked:
            try:
                if overlay is getattr(self, "_main_tools_overlay", None):
                    # Re-apply mapping visibility and order
                    self.apply_menu_settings_main()
                elif overlay is getattr(self, "_overlay", None):
                    self.apply_menu_settings_quick()
            except Exception:
                logging.exception("Failed to reapply menu settings on expand")
        else:
            for w in buttons:
                w.setVisible(False)
        # Adjust the overlay's size to fit the new content; keep left edge stationary
        left_x = overlay.geometry().left()
        overlay.adjustSize()
        overlay.move(left_x, overlay.y())

    def toggle_overlay_collapse(self, checked: bool) -> None:
        """
        Toggles the collapsed state of the quick tools overlay.

        Args:
            checked: The checked state of the collapse button.
        """
        self._set_overlay_collapsed(
            self._overlay, self.tool_widgets, self.collapse_btn, checked
        )

    def toggle_main_tools_collapse(self, checked: bool) -> None:
        """
        Toggles the collapsed state of the main tools overlay.

        Args:
            checked: The checked state of the collapse button.
        """
        overlay = getattr(self, "_main_tools_overlay", None)
        if not overlay:
            return
        buttons = getattr(self, "main_tool_buttons", [])
        self._set_overlay_collapsed(overlay, buttons, self.main_collapse_btn, checked)

    def resizeEvent(self, event: QEvent) -> None:
        """
        Handles the resize event of the widget.

        Args:
            event: The resize event.
        """
        super().resizeEvent(event)
        if not self._did_initial_fit and self.width() > 0 and self.height() > 0:
            self._did_initial_fit = True
            self.fit_requested.emit()

    def refresh_overlay_icons(self, main_window: QWidget) -> None:
        """
        Reload icons for overlay buttons after icon settings changed.

        Args:
            main_window: The main window instance.
        """
        try:
            # Left overlay buttons
            self.zoom_out_btn.setIcon(icon_minus())
            self.zoom_in_btn.setIcon(icon_plus())
            self.fit_btn.setIcon(icon_fit())
            self.handles_btn.setIcon(icon_rotate())
            self.onion_btn.setIcon(icon_onion())
            # Collapse icons respect state
            self.toggle_overlay_collapse(self.collapse_btn.isChecked())

            # Main tools overlay: actions carry icons; ensure collapse icon correct
            self.toggle_main_tools_collapse(self.main_collapse_btn.isChecked())
        except (RuntimeError, AttributeError):
            logging.exception("Failed to refresh overlay icons")
        # Also update icon sizes
        self.apply_icon_size()

    def apply_icon_size(self) -> None:
        """Applies the icon size from settings to all overlay buttons."""
        from ui.settings_keys import ORG, APP, UI_ICON_SIZE
        s = QSettings(ORG, APP)
        try:
            from ui.ui_profile import _int as _to_int
        except Exception:
            _to_int = lambda v, d=32: int(v) if v is not None else d  # type: ignore
        size_val = _to_int(s.value(UI_ICON_SIZE), 32)
        icon_size: int = max(16, min(128, int(size_val)))
        button_size: int = max(28, icon_size + 4)
        # Left overlay
        for btn in [
            self.zoom_out_btn,
            self.zoom_in_btn,
            self.fit_btn,
            self.handles_btn,
            self.onion_btn,
        ]:
            btn.setIconSize(QSize(icon_size, icon_size))
            btn.setFixedSize(button_size, button_size)
        # Main overlay
        for btn in getattr(self, "main_tool_buttons", []):
            btn.setIconSize(QSize(icon_size, icon_size))
            btn.setFixedSize(button_size, button_size)
        # Custom overlay
        try:
            if (
                hasattr(self, "_custom_tools_overlay")
                and self._custom_tools_overlay is not None
            ):
                for btn in self._custom_tools_overlay.findChildren(QToolButton):
                    btn.setIconSize(QSize(icon_size, icon_size))
                    btn.setFixedSize(button_size, button_size)
        except (RuntimeError, AttributeError):
            logging.exception("Failed to apply custom icon sizes")

    def apply_menu_settings_main(self) -> None:
        """Apply visibility settings for main tools overlay based on QSettings."""
        s = QSettings(ORG, APP)

        # Normalize boolean flags via shared helper to handle QSettings quirks
        try:
            from ui.ui_profile import _bool as _to_bool
        except Exception:
            _to_bool = lambda v, d=True: d if v is None else (v in [True, "true", "1"])  # type: ignore

        def is_on(key: str, default: bool = True) -> bool:
            v = s.value(UI_MENU_VIS(MAIN_MENU, key))
            return _to_bool(v, default)

        mapping = getattr(self, "main_tool_buttons_map", {})
        defaults = {
            "save": True,
            "load": True,
            "scene_size": True,
            "background": True,
            "settings": True,
            "reset_scene": True,
            "reset_ui": True,
            "toggle_library": True,
            "toggle_inspector": True,
            "toggle_timeline": True,
            "toggle_custom": True,
        }
        for key, btn in mapping.items():
            btn.setVisible(is_on(key, defaults.get(key, True)))
        # Reorder according to settings
        order = s.value(UI_MENU_ORDER(MAIN_MENU)) or list(mapping.keys())
        if isinstance(order, str):
            order = [k for k in order.split(",") if k]
        # Clear and re-add in order
        try:
            # Remove existing buttons except collapse
            for btn in self.main_tool_buttons:
                self.main_tools_layout.removeWidget(btn)
            self.main_tool_buttons = []
            for key in order:
                btn = mapping.get(key)
                if btn is None:
                    continue
                self.main_tools_layout.addWidget(btn)
                self.main_tool_buttons.append(btn)
            self.main_tools_layout.addWidget(self.main_collapse_btn)
            # Adjust overlay size after relayout
            if (
                hasattr(self, "_main_tools_overlay")
                and self._main_tools_overlay is not None
            ):
                self._main_tools_overlay.adjustSize()
        except (RuntimeError, AttributeError):
            logging.exception("Failed to apply main menu settings")

    def apply_menu_settings_quick(self) -> None:
        """Apply visibility settings for quick overlay buttons based on QSettings."""
        s = QSettings(ORG, APP)

        # Normalize boolean flags via shared helper to handle QSettings quirks
        try:
            from ui.ui_profile import _bool as _to_bool
        except Exception:
            _to_bool = lambda v, d=True: d if v is None else (v in [True, "true", "1"])  # type: ignore

        def is_on(key: str, default: bool = True) -> bool:
            v = s.value(UI_MENU_VIS(QUICK_MENU, key))
            return _to_bool(v, default)

        defaults = {
            "zoom_out": True,
            "zoom_in": True,
            "fit": True,
            "handles": True,
            "onion": True,
        }
        self.quick_buttons_map = {
            "zoom_out": self.zoom_out_btn,
            "zoom_in": self.zoom_in_btn,
            "fit": self.fit_btn,
            "handles": self.handles_btn,
            "onion": self.onion_btn,
        }
        for key, btn in self.quick_buttons_map.items():
            btn.setVisible(is_on(key, defaults.get(key, True)))
        # Reorder
        order = s.value(UI_MENU_ORDER(QUICK_MENU)) or list(self.quick_buttons_map.keys())
        if isinstance(order, str):
            order = [k for k in order.split(",") if k]
        try:
            for btn in [
                self.zoom_out_btn,
                self.zoom_in_btn,
                self.fit_btn,
                self.handles_btn,
                self.onion_btn,
            ]:
                self.layout.removeWidget(btn)
            for key in order:
                btn = self.quick_buttons_map.get(key)
                if btn:
                    self.layout.addWidget(btn)
            # Adjust overlay size to content
            if hasattr(self, "_overlay") and self._overlay is not None:
                self._overlay.adjustSize()
        except (RuntimeError, AttributeError):
            logging.exception("Failed to apply quick menu settings")

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handles the wheel event for zooming.

        Args:
            event: The wheel event.
        """
        if event.modifiers() == Qt.ControlModifier:
            factor: float = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
            self.zoom_requested.emit(factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handles the mouse press event for panning.

        Args:
            event: The mouse press event.
        """
        if event.button() == Qt.MiddleButton:
            self._panning: bool = True
            self._pan_start: QPointF = event.position()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Handles the mouse move event for panning.

        Args:
            event: The mouse move event.
        """
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
        """
        Handles the mouse release event for panning.

        Args:
            event: The mouse release event.
        """
        if event.button() == Qt.MiddleButton and getattr(self, "_panning", False):
            self._panning = False
            self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        Handles the drag enter event for accepting drops from the library.

        Args:
            event: The drag enter event.
        """
        if event.mimeData().hasFormat(LIB_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """
        Handles the drag move event for accepting drops from the library.

        Args:
            event: The drag move event.
        """
        if event.mimeData().hasFormat(LIB_MIME):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Handles the drop event for accepting drops from the library.

        Args:
            event: The drop event.
        """
        if event.mimeData().hasFormat(LIB_MIME):
            try:
                data: bytes = bytes(event.mimeData().data(LIB_MIME))
                payload: Dict[str, Any] = json.loads(data.decode("utf-8"))
                self.item_dropped.emit(payload, event.position())
            except (json.JSONDecodeError, TypeError, ValueError):
                logging.exception("Drop failed")
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
