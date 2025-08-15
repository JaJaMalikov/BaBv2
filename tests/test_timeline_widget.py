import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, QPoint, Qt
from PySide6.QtGui import QWheelEvent

from ui.timeline_widget import TimelineWidget


@pytest.fixture(scope="module")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_add_keyframe_marker_and_navigation(app):
    tw = TimelineWidget()
    tw.add_keyframe_marker(5)
    tw.add_keyframe_marker(10)
    assert 5 in tw._kfs and 10 in tw._kfs

    tw.set_current_frame(7)
    tw.prev_kf_btn.click()
    assert tw._current == 5
    tw.next_kf_btn.click()
    assert tw._current == 10
    tw.next_kf_btn.click()
    assert tw._current == 5


def test_zoom_with_wheel_event(app):
    tw = TimelineWidget()
    tw.resize(400, 100)
    initial = tw._px_per_frame
    ev_in = QWheelEvent(QPointF(0, 0), QPointF(0, 0), QPoint(0, 0), QPoint(0, 120),
                        Qt.NoButton, Qt.ControlModifier, Qt.ScrollBegin, False)
    tw.wheelEvent(ev_in)
    zoomed = tw._px_per_frame
    assert zoomed > initial

    ev_out = QWheelEvent(QPointF(0, 0), QPointF(0, 0), QPoint(0, 0), QPoint(0, -120),
                         Qt.NoButton, Qt.ControlModifier, Qt.ScrollBegin, False)
    tw.wheelEvent(ev_out)
    assert tw._px_per_frame < zoomed
