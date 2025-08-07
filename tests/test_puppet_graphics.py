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


def test_puppet_translation_moves_children(app):
    window = MainWindow()

    torso = window.graphics_items["manu:torse"]
    elbow = window.graphics_items["manu:coude_droite"]

    # Le torse peut être déplacé
    assert torso.flags() & QGraphicsItem.ItemIsMovable

    torso_pivot_before = torso.mapToScene(torso.transformOriginPoint())
    elbow_pivot_before = elbow.mapToScene(elbow.transformOriginPoint())
    dx_before = elbow_pivot_before.x() - torso_pivot_before.x()
    dy_before = elbow_pivot_before.y() - torso_pivot_before.y()

    torso.setPos(torso.x() + 50, torso.y() + 20)

    torso_pivot_after = torso.mapToScene(torso.transformOriginPoint())
    elbow_pivot_after = elbow.mapToScene(elbow.transformOriginPoint())
    assert elbow_pivot_after.x() - torso_pivot_after.x() == pytest.approx(dx_before)
    assert elbow_pivot_after.y() - torso_pivot_after.y() == pytest.approx(dy_before)
