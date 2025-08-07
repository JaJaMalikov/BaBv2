import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QGraphicsItem
import pytest

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_hierarchy_and_pivot(app):
    window = MainWindow()

    upper = window.graphics_items["manu:haut_bras_droite"]
    elbow = window.graphics_items["manu:coude_droite"]
    forearm = window.graphics_items["manu:avant_bras_droite"]

    # Vérifie la hiérarchie parent/enfant
    assert forearm.parentItem() is elbow
    assert elbow.parentItem() is upper

    # Pivots superposés avant rotation
    elbow_pos = elbow.mapToScene(elbow.transformOriginPoint())
    forearm_pos = forearm.mapToScene(forearm.transformOriginPoint())
    assert elbow_pos.x() == pytest.approx(forearm_pos.x())
    assert elbow_pos.y() == pytest.approx(forearm_pos.y())

    # Après rotation du bras, le coude et l\'avant-bras restent solidaires
    upper.setRotation(45)
    elbow_pos_after = elbow.mapToScene(elbow.transformOriginPoint())
    forearm_pos_after = forearm.mapToScene(forearm.transformOriginPoint())
    assert elbow_pos_after.x() == pytest.approx(forearm_pos_after.x())
    assert elbow_pos_after.y() == pytest.approx(forearm_pos_after.y())


def test_z_order_independent_from_hierarchy(app):
    window = MainWindow()

    thigh = window.graphics_items["manu:cuisse_droite"]
    torso = window.graphics_items["manu:torse"]
    shoulder = window.graphics_items["manu:epaule_droite"]

    # La cuisse est derrière son parent et le torse
    assert thigh.flags() & QGraphicsItem.ItemStacksBehindParent
    assert thigh.zValue() < torso.zValue()

    # L'épaule reste devant le torse sans drapeau particulier
    assert not (shoulder.flags() & QGraphicsItem.ItemStacksBehindParent)
    assert shoulder.zValue() > torso.zValue()
