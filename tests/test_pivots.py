import os
import sys

# Ensure Qt runs in offscreen mode
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from PySide6.QtWidgets import QApplication

from core.svg_loader import SvgLoader
from core.puppet_model import Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER
from core.puppet_piece import PuppetPiece


def setup_module(module):
    # Create a QApplication if not already existing
    module.app = QApplication.instance() or QApplication(sys.argv)


def test_pivots_are_positioned_correctly():
    loader = SvgLoader("assets/wesh.svg")
    puppet = Puppet()
    puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)

    for name, member in puppet.members.items():
        offset = loader.get_group_offset(name) or (0, 0)
        pivot_x = member.pivot[0] - offset[0]
        pivot_y = member.pivot[1] - offset[1]
        target_pivot_x, target_pivot_y = puppet.get_handle_target_pivot(name)
        if target_pivot_x is not None and target_pivot_y is not None:
            target_pivot_x -= offset[0]
            target_pivot_y -= offset[1]
        piece = PuppetPiece(
            "assets/wesh.svg",
            name,
            pivot_x=pivot_x,
            pivot_y=pivot_y,
            target_pivot_x=target_pivot_x,
            target_pivot_y=target_pivot_y,
            renderer=loader.renderer,
            grid=None,
        )
        piece.setPos(offset[0], offset[1])
        scene_pivot = piece.mapToScene(piece.transformOriginPoint())
        assert scene_pivot.x() == pytest.approx(member.pivot[0])
        assert scene_pivot.y() == pytest.approx(member.pivot[1])
