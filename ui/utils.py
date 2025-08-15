"""Utility functions for common UI components."""

from typing import Optional, Callable

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QWidget, QToolButton


def make_tool_button(
    parent: QWidget,
    icon: Optional[QIcon] = None,
    tooltip: str = "",
    callback: Optional[Callable[[], None]] = None,
    checkable: bool = False,
    action: Optional[QAction] = None,
    icon_size: int = 32,
    button_size: Optional[int] = None,
) -> QToolButton:
    """Create a standardized ``QToolButton`` for overlay toolbars.

    This helper centralizes the common configuration for tool buttons used
    across the different overlays. It supports both simple icon/callback
    buttons as well as buttons bound to a ``QAction``.

    Parameters
    ----------
    parent:
        Widget that will parent the created button.
    icon:
        Optional ``QIcon`` displayed on the button. Ignored if ``action`` is
        provided.
    tooltip:
        Text shown when the user hovers the button.
    callback:
        Function invoked when the button is clicked. Ignored if ``action`` is
        provided.
    checkable:
        Whether the button maintains an on/off state.
    action:
        Optional ``QAction`` associated with the button instead of a direct
        callback.
    icon_size:
        Size of the icon in pixels.
    button_size:
        Size of the square button. If ``None``, it defaults to
        ``max(28, icon_size + 4)``.

    Returns
    -------
    QToolButton
        The configured tool button ready to be added to a layout.
    """

    btn = QToolButton(parent)
    if action:
        btn.setDefaultAction(action)
    elif icon:
        btn.setIcon(icon)
        if callback:
            btn.clicked.connect(callback)
    elif callback:
        btn.clicked.connect(callback)

    if tooltip:
        btn.setToolTip(tooltip)
    btn.setIconSize(QSize(icon_size, icon_size))
    btn.setCheckable(checkable)
    size = max(28, icon_size + 4) if button_size is None else button_size
    btn.setFixedSize(size, size)
    btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
    btn.setAutoRaise(True)
    return btn
