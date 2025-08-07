from PySide6.QtWidgets import (
    QMainWindow, QGraphicsView, QGraphicsScene, QVBoxLayout,
    QWidget, QGraphicsPixmapItem, QGraphicsEllipseItem
)
from PySide6.QtGui import QPainter, QPixmap, QPen, QColor
from PySide6.QtCore import Qt

from core.scene_model import SceneModel, SceneObject
from core.puppet_piece import PuppetPiece
from core.puppet_model import Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER
from core.svg_loader import SvgLoader

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Borne and the Bayrou - Disco MIX")

        # --- Modèle central ---
        self.scene_model = SceneModel()

        # --- Vue graphique / scène ---
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)

        # --- Layout principal ---
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.addWidget(self.view)
        self.setCentralWidget(main_widget)

        # --- Mapping items graphiques ---
        self.graphics_items = {}
        self.renderers = {}

        # --- Chargement du pantin au démarrage ---
        self.add_puppet("assets/wesh.svg", "manu")

    def add_puppet(self, file_path, puppet_name):
        puppet = Puppet()
        loader = SvgLoader(file_path)
        renderer = loader.renderer
        self.renderers[puppet_name] = renderer
        puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)
        self.scene_model.add_puppet(puppet_name, puppet)
        self._add_puppet_graphics(puppet_name, puppet, file_path, renderer, loader)
        self._fit_scene_to_svg(loader)

    def _add_puppet_graphics(self, puppet_name, puppet, file_path, renderer, loader):
        # Pré-calcul des offsets de chaque groupe
        offsets = {
            name: loader.get_group_offset(name) or (0, 0)
            for name in puppet.members
        }

        # Création des pièces du pantin
        pieces = {}
        for name, member in puppet.members.items():
            offset_x, offset_y = offsets[name]

            # Pivot local relatif à l'origine de l'item
            pivot_x = member.pivot[0] - offset_x
            pivot_y = member.pivot[1] - offset_y

            # Direction du handle : convertie aussi dans le repère local
            target_pivot_x, target_pivot_y = puppet.get_handle_target_pivot(name)
            if target_pivot_x is not None and target_pivot_y is not None:
                target_pivot_x -= offset_x
                target_pivot_y -= offset_y

            piece = PuppetPiece(
                file_path,
                name,
                pivot_x=pivot_x,
                pivot_y=pivot_y,
                target_pivot_x=target_pivot_x,
                target_pivot_y=target_pivot_y,
                renderer=renderer,
                grid=None,
            )
            pieces[name] = piece
            self.graphics_items[f"{puppet_name}:{name}"] = piece

        # Construction de la hiérarchie des items
        for name, piece in pieces.items():
            member = puppet.members[name]
            offset_x, offset_y = offsets[name]
            if member.parent:
                parent_piece = pieces[member.parent.name]
                parent_offset_x, parent_offset_y = offsets[member.parent.name]
                piece.setParentItem(parent_piece)
                # Position relative au parent
                piece.setPos(offset_x - parent_offset_x, offset_y - parent_offset_y)
                # Z relatif pour conserver l'ordre global défini manuellement
                piece.setZValue(member.z_order - member.parent.z_order)
            else:
                self.scene.addItem(piece)
                piece.setPos(offset_x, offset_y)
                piece.setZValue(member.z_order)

    def _fit_scene_to_svg(self, loader):
        if hasattr(loader, "get_svg_viewbox"):
            vb = loader.get_svg_viewbox()
            if vb and len(vb) == 4:
                x, y, w, h = vb
                self.scene.setSceneRect(x, y, w, h)
                self.view.setSceneRect(x, y, w, h)
                self.view.fitInView(x, y, w, h, Qt.KeepAspectRatio)
                self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    # --------- Le reste (inchangé) ---------
    def add_object(self, file_path, obj_name, obj_type="image", x=0, y=0):
        obj = SceneObject(obj_name, obj_type, file_path, x, y)
        self.scene_model.add_object(obj)
        pixmap = QPixmap(file_path)
        item = QGraphicsPixmapItem(pixmap)
        item.setPos(x, y)
        self.scene.addItem(item)
        self.graphics_items[obj_name] = item

    def update_scene_from_model(self):
        pass

    def add_keyframe(self):
        self.scene_model.add_keyframe()

    def go_to_frame(self, index):
        self.scene_model.go_to_frame(index)
        self.update_scene_from_model()

    def export_scene(self, file_path):
        self.scene_model.export_json(file_path)

    def import_scene(self, file_path):
        self.scene_model.import_json(file_path)
        self.update_scene_from_model()
