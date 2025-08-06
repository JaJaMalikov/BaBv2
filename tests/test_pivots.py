import unittest

from core.svg_loader import SvgLoader
from core.puppet_model import Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER

PIVOT_IDS = [
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


class PivotPositionTests(unittest.TestCase):
    def test_pivots_relative_to_group(self):
        loader = SvgLoader("assets/wesh.svg")
        puppet = Puppet()
        puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)
        for name in PIVOT_IDS:
            with self.subTest(member=name):
                member = puppet.members.get(name)
                self.assertIsNotNone(member, f"Member {name} should exist")
                pivot_group = PIVOT_MAP.get(name, name)
                pivot_global = loader.get_pivot(pivot_group)
                offset = loader.get_group_offset(name) or (0, 0)
                expected = (pivot_global[0] - offset[0], pivot_global[1] - offset[1])
                self.assertAlmostEqual(member.pivot[0], expected[0], places=2)
                self.assertAlmostEqual(member.pivot[1], expected[1], places=2)


if __name__ == "__main__":
    unittest.main()
