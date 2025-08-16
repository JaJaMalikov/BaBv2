"""Tests for the StateApplier class."""

import pytest
from PySide6.QtWidgets import QApplication, QGraphicsRectItem

from ui.scene.state_applier import StateApplier


@pytest.fixture(scope="module")
def app():
    """Create a QApplication instance for the tests."""
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


def test_set_object_parent(_app):
    """Test that the object parent is set correctly."""
    applier = StateApplier(win=None)
    child = QGraphicsRectItem()
    parent = QGraphicsRectItem()
    items = {"p:m": parent}

    # pylint: disable=protected-access
    applier._set_object_parent(child, ("p", "m"), items)
    assert child.parentItem() is parent

    # pylint: disable=protected-access
    applier._set_object_parent(child, None, items)
    assert child.parentItem() is None


def test_interpolate_object(_app):
    """Test that object properties are interpolated correctly."""
    applier = StateApplier(win=None)
    gi = QGraphicsRectItem()
    prev = {"x": 0.0, "y": 0.0, "rotation": 0.0, "scale": 1.0, "z": 0}
    nxt = {"x": 10.0, "y": 20.0, "rotation": 90.0, "scale": 2.0, "z": 5}

    # pylint: disable=protected-access
    applier._interpolate_object(gi, prev, nxt, 0.5, None, {})

    assert gi.x() == pytest.approx(5.0)
    assert gi.y() == pytest.approx(10.0)
    assert gi.rotation() == pytest.approx(45.0)
    assert gi.scale() == pytest.approx(1.5)
    assert gi.zValue() == pytest.approx(0)


def test_apply_object_step(_app):
    """Test that object properties are applied correctly for a single step."""
    applier = StateApplier(win=None)
    gi = QGraphicsRectItem()
    prev = {"x": 3.0, "y": 4.0, "rotation": 30.0, "scale": 1.2, "z": 7}

    # pylint: disable=protected-access
    applier._apply_object_step(gi, prev, None, {})

    assert gi.x() == pytest.approx(3.0)
    assert gi.y() == pytest.approx(4.0)
    assert gi.rotation() == pytest.approx(30.0)
    assert gi.scale() == pytest.approx(1.2)
    assert gi.zValue() == pytest.approx(7)
