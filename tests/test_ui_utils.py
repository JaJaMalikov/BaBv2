"""Tests for UI utility helpers."""

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget

from ui.icons import get_icon
from ui.utils import make_tool_button


def test_make_tool_button_basic(_app):
    """Ensure ``make_tool_button`` configures a button correctly."""
    clicked = []

    def on_click():
        clicked.append(True)

    parent = QWidget()
    btn = make_tool_button(
        parent,
        icon=get_icon("plus"),
        tooltip="Add",
        callback=on_click,
        checkable=True,
    )

    assert btn.toolTip() == "Add"
    assert btn.isCheckable()
    assert btn.iconSize() == QSize(32, 32)
    assert btn.width() == max(28, 32 + 4)

    btn.click()
    assert clicked
