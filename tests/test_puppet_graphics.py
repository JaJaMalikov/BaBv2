import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QGraphicsItem
import pytest

import sys
from pathlib import Path

from core.puppet_model import Z_ORDER
from ui.main_window import MainWindow

sys.path.append(str(Path(__file__).resolve().parents[1]))

@pytest.fixture(scope="module")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_hierarchy_and_pivot(app):
    window = MainWindow()

    window.object_manager.add_puppet(str(Path("assets/pantins/manu.svg").resolve()), "manu")

    gis = window.object_manager.graphics_items
    upper = gis["manu:haut_bras_droite"]
    elbow = gis["manu:coude_droite"]
    forearm = gis["manu:avant_bras_droite"]

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
    assert upper.zValue() == Z_ORDER.get("haut_bras_droite", -1)


def test_puppet_translation(app):
    window = MainWindow()
    window.object_manager.add_puppet(str(Path("assets/pantins/manu.svg").resolve()), "manu")
    gis = window.object_manager.graphics_items
    torso = gis["manu:torse"]
    hand = gis["manu:main_droite"]

    # Le torse doit être déplaçable
    assert torso.flags() & QGraphicsItem.ItemIsMovable

    original = hand.mapToScene(hand.transformOriginPoint())
    torso.setPos(torso.x() + 50, torso.y() + 20)
    moved = hand.mapToScene(hand.transformOriginPoint())

    assert moved.x() == pytest.approx(original.x() + 50)
    assert moved.y() == pytest.approx(original.y() + 20)
