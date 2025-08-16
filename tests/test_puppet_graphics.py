"Tests for puppet graphics items."

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QGraphicsItem

from ui.main_window import MainWindow
import core.puppet_model as puppet_model

@pytest.fixture(scope="module")
def app():
    """Create a QApplication instance for the tests."""
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


def test_hierarchy_and_pivot(_app):
    """Test that the puppet hierarchy and pivots are correctly set up."""
    window = MainWindow()

    window.scene_controller.add_puppet(str(Path("assets/pantins/manu.svg").resolve()), "manu")

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

    # Après rotation du bras, le coude et l\avant-bras restent solidaires
    upper.rotate_piece(45)
    elbow_pos_after = elbow.mapToScene(elbow.transformOriginPoint())
    forearm_pos_after = forearm.mapToScene(forearm.transformOriginPoint())
    assert elbow_pos_after.x() == pytest.approx(forearm_pos_after.x())
    assert elbow_pos_after.y() == pytest.approx(forearm_pos_after.y())
    assert elbow.rotation() == pytest.approx(45)
    assert forearm.rotation() == pytest.approx(45)

    # L'ordre d'affichage reste celui défini manuellement
    puppet = window.scene_model.puppets["manu"]
    assert upper.zValue() == puppet.z_order_map.get("haut_bras_droite", -1)


def test_puppet_translation(_app):
    """Test that translating the root of a puppet moves the whole puppet."""
    window = MainWindow()
    window.scene_controller.add_puppet(str(Path("assets/pantins/manu.svg").resolve()), "manu")
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


def test_handle_target_pivot_exception(_app, monkeypatch):
    """Ensure HANDLE_EXCEPTION mapping returns the overridden pivot."""
    window = MainWindow()
    window.scene_controller.add_puppet(str(Path("assets/pantins/manu.svg").resolve()), "manu")
    puppet = window.scene_model.puppets["manu"]

    monkeypatch.setitem(puppet_model.HANDLE_EXCEPTION, "torse", "tete")
    assert puppet.get_handle_target_pivot("torse") == puppet.members["tete"].pivot
