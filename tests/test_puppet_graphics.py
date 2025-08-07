import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
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

    # Vérifie la hiérarchie logique sans impact sur l'affichage
    assert forearm.parent_piece is elbow
    assert elbow.parent_piece is upper

    # Pivots superposés avant rotation
    elbow_pos = elbow.mapToScene(elbow.transformOriginPoint())
    forearm_pos = forearm.mapToScene(forearm.transformOriginPoint())
    assert elbow_pos.x() == pytest.approx(forearm_pos.x())
    assert elbow_pos.y() == pytest.approx(forearm_pos.y())

    # Après rotation du bras, le coude et l\'avant-bras restent solidaires
    upper.rotate_piece(45)
    elbow_pos_after = elbow.mapToScene(elbow.transformOriginPoint())
    forearm_pos_after = forearm.mapToScene(forearm.transformOriginPoint())
    assert elbow_pos_after.x() == pytest.approx(forearm_pos_after.x())
    assert elbow_pos_after.y() == pytest.approx(forearm_pos_after.y())

    # L'ordre d'affichage reste celui défini manuellement
    assert upper.zValue() == -1


def test_move_puppet(app):
    window = MainWindow()
    from PySide6.QtWidgets import QGraphicsItem
    torso = window.graphics_items["manu:torse"]
    arm = window.graphics_items["manu:haut_bras_droite"]

    assert torso.flags() & QGraphicsItem.ItemIsMovable

    arm_before = arm.mapToScene(arm.transformOriginPoint())
    torso.setPos(torso.pos().x() + 40, torso.pos().y() + 25)
    app.processEvents()
    arm_after = arm.mapToScene(arm.transformOriginPoint())

    assert arm_after.x() == pytest.approx(arm_before.x() + 40)
    assert arm_after.y() == pytest.approx(arm_before.y() + 25)
