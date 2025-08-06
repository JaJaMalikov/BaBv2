import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from core.svg_loader import SvgLoader

PIVOTS = [
    "coude_droite",
    "coude_gauche",
    "epaule_droite",
    "epaule_gauche",
    "cou",
    "genou_droite",
    "genou_gauche",
    "hanche_droite",
    "hanche_gauche",
]


@pytest.fixture(scope="module")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_pivot_alignment(app):
    window = MainWindow()
    loader = SvgLoader("assets/wesh.svg")
    for pivot_id in PIVOTS:
        piece = window.graphics_items[f"manu:{pivot_id}"]
        global_pivot = loader.get_pivot(pivot_id)
        mapped = piece.mapToScene(piece.transformOriginPoint())
        assert mapped.x() == pytest.approx(global_pivot[0])
        assert mapped.y() == pytest.approx(global_pivot[1])
