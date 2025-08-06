import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.svg_loader import SvgLoader
from core.puppet_model import Puppet, PARENT_MAP, PIVOT_MAP


def compute_expected_local(loader, group_id, pivot_group):
    bbox = loader.get_group_bounding_box(group_id)
    pivot_global = loader.get_pivot(pivot_group)
    return (
        pivot_global[0] - bbox[0],
        pivot_global[1] - bbox[1],
    )


def test_coude_droite_pivot():
    loader = SvgLoader("assets/wesh.svg")
    puppet = Puppet()
    puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP)
    expected = compute_expected_local(loader, "coude_droite", "coude_droite")
    assert puppet.members["coude_droite"].pivot == pytest.approx(expected)


def test_haut_bras_droite_pivot():
    loader = SvgLoader("assets/wesh.svg")
    puppet = Puppet()
    puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP)
    expected = compute_expected_local(loader, "haut_bras_droite", "epaule_droite")
    assert puppet.members["haut_bras_droite"].pivot == pytest.approx(expected)
