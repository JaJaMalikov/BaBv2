import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QGraphicsRectItem
import pytest

from ui.scene.state_applier import StateApplier


@pytest.fixture(scope="module")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_set_object_parent(app):
    applier = StateApplier(win=None)
    child = QGraphicsRectItem()
    parent = QGraphicsRectItem()
    items = {"p:m": parent}

    applier._set_object_parent(child, ("p", "m"), items)
    assert child.parentItem() is parent

    applier._set_object_parent(child, None, items)
    assert child.parentItem() is None


def test_interpolate_object(app):
    applier = StateApplier(win=None)
    gi = QGraphicsRectItem()
    prev = {"x": 0.0, "y": 0.0, "rotation": 0.0, "scale": 1.0, "z": 0}
    nxt = {"x": 10.0, "y": 20.0, "rotation": 90.0, "scale": 2.0, "z": 5}

    applier._interpolate_object(gi, prev, nxt, 0.5, None, {})

    assert gi.x() == pytest.approx(5.0)
    assert gi.y() == pytest.approx(10.0)
    assert gi.rotation() == pytest.approx(45.0)
    assert gi.scale() == pytest.approx(1.5)
    assert gi.zValue() == pytest.approx(0)


def test_apply_object_step(app):
    applier = StateApplier(win=None)
    gi = QGraphicsRectItem()
    prev = {"x": 3.0, "y": 4.0, "rotation": 30.0, "scale": 1.2, "z": 7}

    applier._apply_object_step(gi, prev, None, {})

    assert gi.x() == pytest.approx(3.0)
    assert gi.y() == pytest.approx(4.0)
    assert gi.rotation() == pytest.approx(30.0)
    assert gi.scale() == pytest.approx(1.2)
    assert gi.zValue() == pytest.approx(7)
