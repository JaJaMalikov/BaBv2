import os
import math
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.append(str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QGraphicsScene

from core.svg_loader import SvgLoader
from core.puppet_model import Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER
from core.puppet_piece import PuppetPiece

app = QApplication.instance() or QApplication([])

SVG_PATH = "assets/wesh.svg"


def build_puppet_items():
    loader = SvgLoader(SVG_PATH)
    puppet = Puppet()
    puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)
    scene = QGraphicsScene()
    items = {}
    for name, member in puppet.members.items():
        tpx, tpy = puppet.get_handle_target_pivot(name)
        piece = PuppetPiece(
            SVG_PATH,
            name,
            pivot_x=member.pivot[0],
            pivot_y=member.pivot[1],
            target_pivot_x=tpx,
            target_pivot_y=tpy,
            renderer=loader.renderer,
            grid=None,
        )
        items[name] = piece
    for name, parent_name in PARENT_MAP.items():
        piece = items.get(name)
        if not piece:
            continue
        parent_piece = items.get(parent_name)
        if parent_piece:
            piece.setParentItem(parent_piece)
        else:
            scene.addItem(piece)
    return scene, items


def test_pivots_within_bounding_box():
    loader = SvgLoader(SVG_PATH)
    pivot_ids = [
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
    for gid in pivot_ids:
        px, py = loader.get_pivot(gid)
        x_min, y_min, x_max, y_max = loader.get_group_bounding_box(gid)
        assert x_min <= px <= x_max
        assert y_min <= py <= y_max


def test_child_follows_parent_rotation():
    scene, items = build_puppet_items()
    parent = items["haut_bras_droite"]
    child = items["avant_bras_droite"]
    ppx, ppy = parent.transformOriginPoint().x(), parent.transformOriginPoint().y()
    cpx, cpy = child.transformOriginPoint().x(), child.transformOriginPoint().y()
    parent_scene_pivot = parent.mapToScene(ppx, ppy)
    child_scene_pivot_before = child.mapToScene(cpx, cpy)
    dist_before = math.hypot(
        child_scene_pivot_before.x() - parent_scene_pivot.x(),
        child_scene_pivot_before.y() - parent_scene_pivot.y(),
    )

    parent.setRotation(90)
    child_scene_pivot_after = child.mapToScene(cpx, cpy)
    dist_after = math.hypot(
        child_scene_pivot_after.x() - parent_scene_pivot.x(),
        child_scene_pivot_after.y() - parent_scene_pivot.y(),
    )
    assert not math.isclose(dist_before, 0)
    assert math.isclose(dist_before, dist_after, rel_tol=1e-6)
    assert not math.isclose(
        child_scene_pivot_before.x(), child_scene_pivot_after.x()
    ) or not math.isclose(
        child_scene_pivot_before.y(), child_scene_pivot_after.y()
    )
