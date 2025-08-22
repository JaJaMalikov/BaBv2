from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from PySide6.QtCore import QSettings


def _clear_geometry_keys() -> None:
    s = QSettings("JaJa", "Macronotron")
    for key in [
        "geometry/mainwindow",
        "geometry/library",
        "geometry/inspector",
        "geometry/view_toolbar",
        "geometry/main_toolbar",
        "layout/timeline_visible",
    ]:
        s.remove(key)


def test_overlay_geometry_persist_roundtrip(_app):
    # Ensure a clean slate
    _clear_geometry_keys()

    # First window: set specific geometries and save
    win1 = MainWindow()
    win1.show()
    QApplication.processEvents()

    lib_rect = QRect(20, 50, 345, 400)
    insp_rect = QRect(700, 60, 360, 420)

    win1.set_library_overlay_visible(True)
    win1.set_inspector_overlay_visible(True)
    QApplication.processEvents()

    win1.library_overlay.setGeometry(lib_rect)
    win1.inspector_overlay.setGeometry(insp_rect)
    QApplication.processEvents()

    win1.save_settings()

    # Second window: load and verify geometries
    win2 = MainWindow()
    win2.show()
    QApplication.processEvents()

    # Overlays should be visible and have the same geometry
    assert win2.library_overlay.isVisible()
    assert win2.inspector_overlay.isVisible()
    assert win2.library_overlay.geometry() == lib_rect
    assert win2.inspector_overlay.geometry() == insp_rect

    # Cleanup geometry keys to avoid side effects across tests
    _clear_geometry_keys()
