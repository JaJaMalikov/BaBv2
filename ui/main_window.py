from PySide6.QtWidgets import (
    QMainWindow,
    QGraphicsView,
    QGraphicsScene,
    QVBoxLayout,
    QWidget,
    QGraphicsPixmapItem,
    QGraphicsItem,
    QDockWidget,
    QFileDialog,
)
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import Qt, QTimer

from core.scene_model import SceneModel, SceneObject
from core.puppet_piece import PuppetPiece
from core.puppet_model import Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER
from core.svg_loader import SvgLoader
from ui.ui_menu import Ui_MainWindow
from ui.timeline_widget import TimelineWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Borne and the Bayrou - Disco MIX")
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

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

        # --- Timeline ---
        self.timeline_dock = QDockWidget("Timeline", self)
        self.timeline_widget = TimelineWidget()
        self.timeline_dock.setWidget(self.timeline_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.timeline_dock)
        
        # --- Timer pour la lecture ---
        self.playback_timer = QTimer(self)
        self.playback_timer.setInterval(1000 // 24) # 24 FPS
        self.playback_timer.timeout.connect(self.next_frame)

        # Connexions
        self.timeline_widget.addKeyframeClicked.connect(self.add_keyframe)
        self.timeline_widget.frameChanged.connect(self.go_to_frame)
        self.timeline_widget.playClicked.connect(self.play_animation)
        self.timeline_widget.pauseClicked.connect(self.pause_animation)
        self.ui.actionSauvegarder.triggered.connect(self.save_scene)
        self.ui.actionCharger_2.triggered.connect(self.load_scene)

        # --- Mapping items graphiques ---
        self.graphics_items = {}
        self.renderers = {}

        # --- Chargement du pantin au démarrage ---
        self.add_puppet("assets/wesh.svg", "manu")

    def save_scene(self):
        filePath, _ = QFileDialog.getSaveFileName(self, "Sauvegarder la scène", "", "JSON Files (*.json)")
        if filePath:
            self.export_scene(filePath)
            print(f"Scène sauvegardée dans {filePath}")

    def load_scene(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Charger une scène", "", "JSON Files (*.json)")
        if filePath:
            self.import_scene(filePath)
            print(f"Scène chargée depuis {filePath}")

    def play_animation(self):
        self.playback_timer.start()

    def pause_animation(self):
        self.playback_timer.stop()

    def next_frame(self):
        current_frame = self.scene_model.current_frame
        new_frame = current_frame + 1
        if new_frame > self.timeline_widget.slider.maximum():
            new_frame = 0 # Loop
        self.timeline_widget.set_current_frame(new_frame)

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
        offsets = {name: loader.get_group_offset(name) or (0, 0) for name in puppet.members}
        pieces = {}
        for name, member in puppet.members.items():
            offset_x, offset_y = offsets[name]
            pivot_x = member.pivot[0] - offset_x
            pivot_y = member.pivot[1] - offset_y
            target_pivot_x, target_pivot_y = puppet.get_handle_target_pivot(name)
            if target_pivot_x is not None and target_pivot_y is not None:
                target_pivot_x -= offset_x
                target_pivot_y -= offset_y
            piece = PuppetPiece(
                file_path, name, pivot_x, pivot_y, 
                target_pivot_x, target_pivot_y, renderer, None
            )
            piece.setZValue(member.z_order)
            pieces[name] = piece
            self.graphics_items[f"{puppet_name}:{name}"] = piece

        for name, piece in pieces.items():
            member = puppet.members[name]
            if member.parent:
                parent_piece = pieces[member.parent.name]
                parent_member = puppet.members[member.parent.name]
                rel_x = member.pivot[0] - parent_member.pivot[0]
                rel_y = member.pivot[1] - parent_member.pivot[1]
                piece.set_parent_piece(parent_piece, rel_x, rel_y)
            else:
                piece.setPos(offsets[name][0], offsets[name][1])
                piece.setFlag(QGraphicsItem.ItemIsMovable, True)
                piece.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        for piece in pieces.values():
            self.scene.addItem(piece)
        for piece in pieces.values():
            if piece.parent_piece:
                piece.update_transform_from_parent()

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

    def add_object(self, file_path, obj_name, obj_type="image", x=0, y=0):
        obj = SceneObject(obj_name, obj_type, file_path, x, y)
        self.scene_model.add_object(obj)
        pixmap = QPixmap(file_path)
        item = QGraphicsPixmapItem(pixmap)
        item.setPos(x, y)
        self.scene.addItem(item)
        self.graphics_items[obj_name] = item

    def update_scene_from_model(self):
        index = self.scene_model.current_frame
        keyframes = self.scene_model.keyframes

        if not keyframes:
            return

        # --- Recherche des keyframes environnantes ---
        prev_kf_index = -1
        next_kf_index = -1
        sorted_indices = sorted(keyframes.keys())

        for i in sorted_indices:
            if i <= index:
                prev_kf_index = i
            if i > index:
                next_kf_index = i
                break

        # --- Interpolation ---
        if prev_kf_index != -1 and next_kf_index != -1 and prev_kf_index != next_kf_index:
            # On est ENTRE deux keyframes
            prev_kf = keyframes[prev_kf_index]
            next_kf = keyframes[next_kf_index]
            
            # Calcul du ratio d'interpolation
            ratio = (index - prev_kf_index) / (next_kf_index - prev_kf_index)

            for puppet_name, puppet in self.scene_model.puppets.items():
                prev_pose = prev_kf.puppets.get(puppet_name, {})
                next_pose = next_kf.puppets.get(puppet_name, {})

                for member_name in puppet.members:
                    prev_state = prev_pose.get(member_name)
                    next_state = next_pose.get(member_name)
                    if not prev_state or not next_state:
                        continue

                    # Interpolation de la rotation
                    prev_rot = prev_state['rotation']
                    next_rot = next_state['rotation']
                    interp_rot = prev_rot + (next_rot - prev_rot) * ratio

                    piece = self.graphics_items[f"{puppet_name}:{member_name}"]
                    piece.local_rotation = interp_rot

                    # Interpolation de la position (pour la racine)
                    if not piece.parent_piece:
                        prev_pos = prev_state['pos']
                        next_pos = next_state['pos']
                        interp_x = prev_pos[0] + (next_pos[0] - prev_pos[0]) * ratio
                        interp_y = prev_pos[1] + (next_pos[1] - prev_pos[1]) * ratio
                        piece.setPos(interp_x, interp_y)

        else:
            # On est sur une keyframe ou en dehors de la plage
            target_kf_index = prev_kf_index if prev_kf_index != -1 else next_kf_index
            if target_kf_index == -1:
                return # Aucune keyframe à afficher

            kf = keyframes[target_kf_index]
            for puppet_name, puppet_state in kf.puppets.items():
                for member_name, member_state in puppet_state.items():
                    piece = self.graphics_items[f"{puppet_name}:{member_name}"]
                    piece.local_rotation = member_state['rotation']
                    if not piece.parent_piece:
                        pos = member_state['pos']
                        piece.setPos(pos[0], pos[1])

        # --- Mise à jour de la hiérarchie graphique ---
        for puppet_name, puppet in self.scene_model.puppets.items():
            for root_member in puppet.get_root_members():
                root_piece = self.graphics_items[f"{puppet_name}:{root_member.name}"]
                root_piece.setRotation(root_piece.local_rotation)
                for child in root_piece.children:
                    child.update_transform_from_parent()

    def add_keyframe(self, frame_index):
        kf = self.scene_model.add_keyframe(frame_index)
        
        for puppet_name, puppet in self.scene_model.puppets.items():
            puppet_state = {}
            for member_name in puppet.members:
                item_key = f"{puppet_name}:{member_name}"
                piece = self.graphics_items[item_key]
                puppet_state[member_name] = {
                    'rotation': piece.local_rotation,
                    'pos': (piece.x(), piece.y())
                }
            kf.puppets[puppet_name] = puppet_state

        self.timeline_widget.add_keyframe_marker(frame_index)
        print(f"Keyframe ajouté à l'index {frame_index}")

    def go_to_frame(self, index):
        self.scene_model.go_to_frame(index)
        self.update_scene_from_model()

    def export_scene(self, file_path):
        self.scene_model.export_json(file_path)

    def import_scene(self, file_path):
        self.scene_model.import_json(file_path)
        self.timeline_widget.clear_keyframes()
        for kf_index in self.scene_model.keyframes:
            self.timeline_widget.add_keyframe_marker(kf_index)
        self.update_scene_from_model()
