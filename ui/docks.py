"""Dock setup utilities."""

from __future__ import annotations

import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow, QWidget as _QW

from ui.views.timeline_widget import TimelineWidget


def setup_timeline_dock(main_window: QMainWindow) -> TimelineWidget:
    """Create the timeline dock on ``main_window`` and return the widget."""
    timeline_dock: QDockWidget = QDockWidget("", main_window)
    timeline_dock.setObjectName("dock_timeline")
    timeline_widget: TimelineWidget = TimelineWidget()
    timeline_dock.setWidget(timeline_widget)
    timeline_dock.setFeatures(QDockWidget.DockWidgetClosable)
    try:
        timeline_dock.setTitleBarWidget(_QW())
    except (ImportError, RuntimeError) as e:
        logging.debug("Custom title bar not set on dock: %s", e)
    main_window.timeline_dock = timeline_dock
    main_window.addDockWidget(Qt.BottomDockWidgetArea, timeline_dock)
    return timeline_widget
