import os
import math
import sys
import pathlib
import pytest
from PySide6.QtWidgets import QApplication

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.main_window import MainWindow
from core.svg_loader import SvgLoader


@pytest.fixture(scope="module")
def app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_pivot_alignment_and_hierarchy(app):
    window = MainWindow()
    puppet = window.scene_model.puppets["manu"]
    loader = SvgLoader("assets/wesh.svg")
    piece = window.graphics_items["manu:coude_droite"]
    member = puppet.members["coude_droite"]
    offset = loader.get_group_offset("coude_droite")
    assert piece.transformOriginPoint().x() == pytest.approx(member.pivot[0] - offset[0], abs=1e-2)
    assert piece.transformOriginPoint().y() == pytest.approx(member.pivot[1] - offset[1], abs=1e-2)
    parent_piece = window.graphics_items["manu:haut_bras_droite"]
    assert piece.parentItem() is parent_piece
    parent_pivot = parent_piece.mapToScene(parent_piece.transformOriginPoint())
    child_pivot = piece.mapToScene(piece.transformOriginPoint())
    v = child_pivot - parent_pivot
    dist = (v.x() ** 2 + v.y() ** 2) ** 0.5
    parent_piece.setRotation(90)
    parent_pivot2 = parent_piece.mapToScene(parent_piece.transformOriginPoint())
    child_pivot2 = piece.mapToScene(piece.transformOriginPoint())
    v2 = child_pivot2 - parent_pivot2
    dist2 = (v2.x() ** 2 + v2.y() ** 2) ** 0.5
    assert dist2 == pytest.approx(dist, abs=1e-2)
    angle = math.degrees(math.atan2(v.y(), v.x()))
    angle2 = math.degrees(math.atan2(v2.y(), v2.x()))
    assert (angle2 - angle) == pytest.approx(90, abs=1)
    window.close()
