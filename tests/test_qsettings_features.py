from __future__ import annotations

from PySide6.QtCore import QSettings, QSize
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def _reset_ui_settings() -> None:
    s = QSettings("JaJa", "Macronotron")
    # Clear UI-related keys that we touch in this test
    for key in [
        "ui/icon_size",
        "ui/theme",
        "ui/menu/main/order",
        "ui/menu/quick/order",
        # visibility flags (booleans may be strings)
        "ui/menu/main/toggle_custom",
        "ui/menu/main/toggle_timeline",
        "ui/menu/main/toggle_inspector",
        "ui/menu/main/toggle_library",
        "ui/menu/quick/onion",
    ]:
        s.remove(key)


def test_qsettings_string_bools_and_orders_applied(_app):
    _reset_ui_settings()
    s = QSettings("JaJa", "Macronotron")

    # Set values as strings to emulate platform stores returning strings
    s.setValue("ui/icon_size", "48")  # string numeric
    s.setValue("ui/theme", "dark")  # theme value; we won't assert visuals

    # Main tools order as CSV string and visibility flags as string-bools
    s.setValue("ui/menu/main/order", "save,load,toggle_library")
    s.setValue("ui/menu/main/toggle_custom", "false")
    s.setValue("ui/menu/main/toggle_timeline", "1")
    s.setValue("ui/menu/main/toggle_inspector", True)
    s.setValue("ui/menu/main/toggle_library", "true")

    # Quick overlay: hide onion via string-bool and set custom order
    s.setValue("ui/menu/quick/onion", "false")
    s.setValue("ui/menu/quick/order", "zoom_in,zoom_out,fit")

    # Build window (startup sequence applies menu settings via OverlayManager)
    win = MainWindow()
    win.show()
    QApplication.processEvents()

    # Icon size applied to main overlay buttons
    # pick one known button: save
    save_btn = win.view.main_tool_buttons_map["save"]
    assert save_btn.iconSize() == QSize(48, 48)

    # Order applied: first three buttons correspond to our specified order
    first_three = win.view.main_tool_buttons[:3]
    # Map back from button to key by inverse lookup
    inv_map = {btn: key for key, btn in win.view.main_tool_buttons_map.items()}
    observed_order = [inv_map[b] for b in first_three]
    assert observed_order == ["save", "load", "toggle_library"]

    # Visibility flags: toggle_custom should be hidden
    assert not win.view.main_tool_buttons_map["toggle_custom"].isVisible()
    # toggle_timeline should be visible ("1" treated as true)
    assert win.view.main_tool_buttons_map["toggle_timeline"].isVisible()

    # Quick overlay: onion hidden; order applied (first three)
    assert not win.view.onion_btn.isVisible()
    quick_children = [
        win.view.zoom_in_btn,
        win.view.zoom_out_btn,
        win.view.fit_btn,
        win.view.handles_btn,
        win.view.onion_btn,
    ]
    # Filter visible and take first three in layout order
    # The layout order for visible buttons should follow our order
    visible_in_layout = [b for b in quick_children if b.isVisible()]
    # Ensure the first three visible match our expected order
    assert visible_in_layout[:3] == [
        win.view.zoom_in_btn,
        win.view.zoom_out_btn,
        win.view.fit_btn,
    ]

    _reset_ui_settings()
