from PySide6.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene, QVBoxLayout, QWidget
from PySide6.QtGui import QPainter

from core.scene_model import SceneModel, SceneObject
from core.puppet_piece import PuppetPiece
from core.puppet_model import Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER  # déjà prêt !

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Borne and the Bayrou - Disco MIX")

        # --- Modèle central (toute la logique) ---
        self.scene_model = SceneModel()

        # --- Partie graphique / Vue ---
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)

        # --- Layout et Widgets ---
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.addWidget(self.view)
        self.setCentralWidget(main_widget)

        # --- Mapping nom -> QGraphicsItem (pour synchronisation rapide) ---
        self.graphics_items = {}
        self.renderers = {}

        # --- Init : tu peux charger une scène ou ajouter un pantin de démo ici ---
        self.add_puppet("assets/wesh.svg", "manu")

    # -----------------------------------------------
    # AJOUT/CHARGEMENT DE PANTIN OU OBJET
    # -----------------------------------------------

    def add_puppet(self, file_path, puppet_name):
        # 1. Crée le Puppet (via le modèle) et le SvgLoader
        puppet = Puppet()
        from core.svg_loader import SvgLoader
        loader = SvgLoader(file_path)
        renderer = loader.renderer  # Le renderer partagé
        self.renderers[puppet_name] = renderer  # Conserver la référence !
        puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)
        self.scene_model.add_puppet(puppet_name, puppet)

        # 2. Crée tous les PuppetPiece et ajoute à la scène
        self._add_puppet_graphics(puppet_name, puppet, file_path, renderer, loader)

    def _add_puppet_graphics(self, puppet_name, puppet, file_path, renderer, loader):
        pieces = {}
        for name, member in puppet.members.items():
            target_pivot_x, target_pivot_y = puppet.get_handle_target_pivot(name)

            piece = PuppetPiece(
                file_path, name,
                pivot_x=member.pivot[0],
                pivot_y=member.pivot[1],
                target_pivot_x=target_pivot_x,
                target_pivot_y=target_pivot_y,
                renderer=renderer,  # Utilisation du renderer partagé
                grid=None,
            )
            piece.setZValue(member.z_order)

            # Positionnement de la pièce
            offset = loader.get_group_offset(name) or (0, 0)

            if member.parent:
                parent_piece = pieces.get(member.parent.name)
                if parent_piece:
                    parent_offset = loader.get_group_offset(member.parent.name) or (0, 0)
                    # Position relative par rapport au parent
                    relative_x = offset[0] - parent_offset[0]
                    relative_y = offset[1] - parent_offset[1]
                    piece.setPos(relative_x, relative_y)
                    piece.setParentItem(parent_piece)
                else:
                    # Si le parent n'est pas trouvé, on le place en absolu
                    self.scene.addItem(piece)
                    piece.setPos(offset[0], offset[1])
            else:
                # Position absolue pour les pièces racines
                self.scene.addItem(piece)
                piece.setPos(offset[0], offset[1])

            pieces[name] = piece
            self.graphics_items[f"{puppet_name}:{name}"] = piece
        # Option : conserver pieces pour manip plus tard

    def add_object(self, file_path, obj_name, obj_type="image", x=0, y=0):
        # Ajout dans le modèle
        obj = SceneObject(obj_name, obj_type, file_path, x, y)
        self.scene_model.add_object(obj)
        # Création graphique selon type
        # Ici, pour PNG :
        from PySide6.QtWidgets import QGraphicsPixmapItem
        from PySide6.QtGui import QPixmap
        pixmap = QPixmap(file_path)
        item = QGraphicsPixmapItem(pixmap)
        item.setPos(x, y)
        self.scene.addItem(item)
        self.graphics_items[obj_name] = item

    # -----------------------------------------------
    # SYNCHRONISATION SCÈNE <-> MODÈLE
    # -----------------------------------------------

    def update_scene_from_model(self):
        # À appeler à chaque changement de frame, d’attache, etc.
        # - Bouge tous les objets graphiques selon les states du modèle
        # - Gère les attaches (si un objet est enfant d’un membre d’un pantin)
        # - etc.
        # (à compléter au fur et à mesure)
        pass

    # -----------------------------------------------
    # FONCTIONS TIMELINE / KEYFRAME / FRAME NAV
    # -----------------------------------------------

    def add_keyframe(self):
        self.scene_model.add_keyframe()

    def go_to_frame(self, index):
        self.scene_model.go_to_frame(index)
        self.update_scene_from_model()

    # -----------------------------------------------
    # IMPORT/EXPORT
    # -----------------------------------------------

    def export_scene(self, file_path):
        self.scene_model.export_json(file_path)

    def import_scene(self, file_path):
        self.scene_model.import_json(file_path)
        self.update_scene_from_model()

    # -----------------------------------------------
    # INTERACTIONS / MENUS / OUTILS À AJOUTER
    # (Panneaux, context menus, raccourcis, ...)
    # -----------------------------------------------
    # (À compléter en fonction de tes besoins UI)

