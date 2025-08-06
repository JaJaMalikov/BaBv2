import os
import unittest

# Utiliser le rendu hors écran de Qt
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from core.svg_loader import SvgLoader
from core.puppet_model import Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER
from ui.main_window import MainWindow

# Crée une instance QApplication unique pour tous les tests
app = QApplication.instance() or QApplication([])


class TestPuppetModel(unittest.TestCase):
    def setUp(self):
        loader = SvgLoader("assets/wesh.svg")
        self.puppet = Puppet()
        self.puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)

    def test_pivots_inside_bbox(self):
        """Chaque pivot doit se situer dans la bounding box correspondante."""
        for name, member in self.puppet.members.items():
            x_min, y_min, x_max, y_max = member.bbox
            px, py = member.pivot
            with self.subTest(member=name):
                self.assertGreaterEqual(px, x_min)
                self.assertLessEqual(px, x_max)
                self.assertGreaterEqual(py, y_min)
                self.assertLessEqual(py, y_max)


class TestPuppetGraphics(unittest.TestCase):
    def setUp(self):
        # La fenêtre crée et charge le pantin automatiquement
        self.window = MainWindow()

    def test_hierarchy(self):
        """Les pièces graphiques doivent respecter la hiérarchie parent/enfant."""
        puppet = self.window.scene_model.puppets["manu"]
        for name, member in puppet.members.items():
            item = self.window.graphics_items[f"manu:{name}"]
            if member.parent:
                parent_name = member.parent.name
                parent_item = self.window.graphics_items[f"manu:{parent_name}"]
                self.assertIs(item.parentItem(), parent_item, msg=name)
            else:
                self.assertIsNone(item.parentItem(), msg=name)
