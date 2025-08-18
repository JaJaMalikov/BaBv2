"""Tests for the TimelineWidget class."""

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication

from ui.views.timeline_widget import TimelineWidget


@pytest.fixture(scope="module")
def app():
    """Create a QApplication instance for the tests."""
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


def test_add_keyframe_marker_and_navigation(_app):
    """Test that keyframe markers can be added and navigated."""
    tw = TimelineWidget()
    tw.add_keyframe_marker(5)
    tw.add_keyframe_marker(10)
    # pylint: disable=protected-access
    assert 5 in tw._kfs and 10 in tw._kfs

    tw.set_current_frame(7)
    tw.prev_kf_btn.click()
    # pylint: disable=protected-access
    assert tw._current == 5
    tw.next_kf_btn.click()
    # pylint: disable=protected-access
    assert tw._current == 10
    tw.next_kf_btn.click()
    # pylint: disable=protected-access
    assert tw._current == 5


def test_zoom_with_wheel_event(_app):
    """Test that the timeline can be zoomed with the wheel event."""
    tw = TimelineWidget()
    tw.resize(400, 100)
    # pylint: disable=protected-access
    initial = tw._px_per_frame
    ev_in = QWheelEvent(
        QPointF(0, 0),
        QPointF(0, 0),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.NoButton,
        Qt.ControlModifier,
        Qt.ScrollBegin,
        False,
    )
    tw.wheelEvent(ev_in)
    # pylint: disable=protected-access
    zoomed = tw._px_per_frame
    assert zoomed > initial

    ev_out = QWheelEvent(
        QPointF(0, 0),
        QPointF(0, 0),
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.NoButton,
        Qt.ControlModifier,
        Qt.ScrollBegin,
        False,
    )
    tw.wheelEvent(ev_out)
    # pylint: disable=protected-access
    assert tw._px_per_frame < zoomed
