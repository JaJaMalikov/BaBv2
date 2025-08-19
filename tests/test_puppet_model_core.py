from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pytest

from core.puppet_model import (
    Puppet,
    PuppetMember,
    compute_child_map,
    normalize_variants,
)


class _StubSvgLoader:
    """Minimal stub for SvgLoader used to unit-test Puppet.build_from_svg.

    Avoids Qt dependencies by providing only the methods used by build_from_svg.
    """

    def __init__(self, groups: List[str], pivots: Dict[str, Tuple[float, float]] | None = None):
        self._groups = list(groups)
        self._pivots = dict(pivots or {})

    def get_groups(self) -> List[str]:
        return list(self._groups)

    def get_group_bounding_box(self, group_id: str):  # type: ignore[override]
        # Return a non-null bbox shape so that pivot computation would be meaningful if called.
        return 0.0, 0.0, 10.0, 10.0

    def get_pivot(self, group_id: str) -> Tuple[float, float]:  # type: ignore[override]
        return self._pivots.get(group_id, (5.0, 5.0))


def test_compute_child_map_deterministic_order():
    # Given an insertion-ordered mapping, the child list should preserve order
    parent_map: Dict[str, Optional[str]] = {
        "a": None,
        "b": "a",
        "c": "a",
        "d": "b",
    }
    cmap = compute_child_map(parent_map)
    assert cmap["a"] == ["b", "c"]
    assert cmap["b"] == ["d"]


def test_normalize_variants_and_properties_bridge():
    raw = {
        "slot": [
            "varA",
            {"name": "varB", "z": 7},
            ["varC", 9],
            {"bad": "shape"},
            123,
        ]
    }
    names, zmap = normalize_variants(raw)
    assert names["slot"] == ["varA", "varB", "varC"]
    assert zmap["varB"] == 7
    assert zmap["varC"] == 9

    p = Puppet()
    # Bridge setters should accept plain dicts and be reflected on getters
    p.variants = names
    p.variant_z = zmap
    assert p.variants == names
    assert p.variant_z == zmap


def test_build_hierarchy_with_stub_loader():
    # Minimal puppet config for a small chain: torse -> cou -> tete
    p = Puppet()
    p.parent_map = {"torse": None, "cou": "torse", "tete": "cou"}
    p.pivot_map = {}
    p.z_order_map = {"torse": 0, "cou": 0, "tete": 1}
    p.child_map = dict(compute_child_map(p.parent_map))

    pivots = {
        "torse": (10.0, 10.0),
        "cou": (10.0, 5.0),
        "tete": (10.0, 0.0),
    }
    loader = _StubSvgLoader(groups=list(p.parent_map.keys()), pivots=pivots)

    p.build_from_svg(loader)  # type: ignore[arg-type]

    # Members exist
    assert set(p.members.keys()) == {"torse", "cou", "tete"}
    # Parent relationships
    assert p.members["cou"].parent is p.members["torse"]
    assert p.members["tete"].parent is p.members["cou"]
    # Relative offsets (child.pivot - parent.pivot)
    assert p.members["cou"].rel_pos == (
        pivots["cou"][0] - pivots["torse"][0],
        pivots["cou"][1] - pivots["torse"][1],
    )
    assert p.members["tete"].rel_pos == (
        pivots["tete"][0] - pivots["cou"][0],
        pivots["tete"][1] - pivots["cou"][1],
    )
