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
    QInputDialog,
    QGraphicsRectItem,
    QGraphicsTextItem
)
from PySide6.QtGui import QPainter, QPixmap, QAction, QColor, QPen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtSvgWidgets import QGraphicsSvgItem

from core.scene_model import SceneModel, SceneObject
from core.puppet_piece import PuppetPiece
from core.puppet_model import Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER
from core.svg_loader import SvgLoader
from ui.ui_menu import Ui_MainWindow
from ui.timeline_widget import TimelineWidget
from ui.inspector_widget import InspectorWidget

class ZoomableView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.main_window = None # Will be set by MainWindow

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            factor = 1.1 if delta > 0 else 1 / 1.1
            if self.main_window:
                self.main_window.zoom(factor)
        else:
            super().wheelEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Borne and the Bayrou - Disco MIX")
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.scene_model = SceneModel()
        self.graphics_items = {}
        self.renderers = {}
        self.background_item = None
        self.puppet_scales = {}
        self.puppet_paths = {}

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.scene_model.scene_width, self.scene_model.scene_height)
        
        self.view = ZoomableView(self.scene, self)
        self.view.main_window = self # Set the reference to MainWindow
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.addWidget(self.view)
        self.setCentralWidget(main_widget)

        self.timeline_dock = QDockWidget("Timeline", self)
        self.timeline_widget = TimelineWidget()
        self.timeline_dock.setWidget(self.timeline_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.timeline_dock)

        self.inspector_dock = QDockWidget("Inspector", self)
        self.inspector_widget = InspectorWidget(self)
        self.inspector_dock.setWidget(self.inspector_widget)
        self.inspector_dock.setFloating(True)
        self.addDockWidget(Qt.RightDockWidgetArea, self.inspector_dock)
        self.inspector_dock.hide()

        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.next_frame)
        self.set_fps(self.scene_model.fps)

        self.setup_menus()
        self.connect_signals()
        self._setup_scene_visuals() # Setup scene border and text

        self.add_puppet("assets/manululu.svg", "manu")
        self.inspector_widget.refresh()
        self._update_timeline_ui_from_model()
        self.center_on_puppet() # Center view on puppet at startup
        self._update_zoom_status() # Initial zoom status

    def setup_menus(self):
        self.ui.menuToggle_Inspector.clear()
        self.ui.menuToggle_Inspector.addAction(self.inspector_dock.toggleViewAction())
        self.ui.menuToggle_Timeline.clear()
        self.ui.menuToggle_Timeline.addAction(self.timeline_dock.toggleViewAction())
        self.ui.menuToggle_Transformation.clear()
        toggle_handles_action = QAction("Afficher les poignées", self, checkable=True)
        toggle_handles_action.setChecked(False)
        toggle_handles_action.toggled.connect(self.toggle_rotation_handles)
        self.ui.menuToggle_Transformation.addAction(toggle_handles_action)

    def connect_signals(self):
        self.timeline_widget.addKeyframeClicked.connect(self.add_keyframe)
        self.timeline_widget.deleteKeyframeClicked.connect(self.delete_keyframe)
        self.timeline_widget.frameChanged.connect(self.go_to_frame)
        self.timeline_widget.playClicked.connect(self.play_animation)
        self.timeline_widget.pauseClicked.connect(self.pause_animation)
        self.timeline_widget.fpsChanged.connect(self.set_fps)
        self.timeline_widget.rangeChanged.connect(self.set_range)

        self.ui.actionSauvegarder.triggered.connect(self.save_scene)
        self.ui.actionCharger_2.triggered.connect(self.load_scene)
        self.ui.actionTaille_Sc_ne.triggered.connect(self.set_scene_size)
        self.ui.actionBackground.triggered.connect(self.set_background)

        # Zoom actions
        self.zoom_factor = 1.0 # Initialize zoom_factor before connecting zoom actions
        self.ui.action_9.triggered.connect(lambda: self.zoom(1.25))
        self.ui.action_10.triggered.connect(lambda: self.zoom(0.8))
        self.ui.actionFit.triggered.connect(self.fit_to_view)
        self.ui.actionCenter.triggered.connect(self.center_on_puppet)

    def _setup_scene_visuals(self):
        self.scene_border_item = QGraphicsRectItem()
        self.scene_size_text_item = QGraphicsTextItem()
        self.scene.addItem(self.scene_border_item)
        self.scene.addItem(self.scene_size_text_item)
        self._update_scene_visuals()

    def _update_scene_visuals(self):
        rect = self.scene.sceneRect()
        pen = QPen(QColor(100, 100, 100), 2, Qt.DashLine)
        self.scene_border_item.setPen(pen)
        self.scene_border_item.setRect(rect)

        width = self.scene_model.scene_width
        height = self.scene_model.scene_height
        self.scene_size_text_item.setPlainText(f"{width}x{height}")
        self.scene_size_text_item.setDefaultTextColor(QColor(150, 150, 150))
        text_rect = self.scene_size_text_item.boundingRect()
        self.scene_size_text_item.setPos(rect.right() - text_rect.width() - 10, rect.bottom() - text_rect.height() - 10)

    def _update_zoom_status(self):
        self.statusBar().showMessage(f"Zoom: {self.zoom_factor:.0%}")

    def zoom(self, factor):
        self.view.scale(factor, factor)
        self.zoom_factor *= factor
        self._update_zoom_status()

    def fit_to_view(self):
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.zoom_factor = self.view.transform().m11()
        self._update_zoom_status()

    def center_on_puppet(self):
        puppet_root = self.graphics_items.get("manu:torse")
        if puppet_root:
            self.view.centerOn(puppet_root)

    def set_scene_size(self):
        width, ok1 = QInputDialog.getInt(self, "Taille de la scène", "Largeur:", self.scene_model.scene_width, 1)
        if ok1:
            height, ok2 = QInputDialog.getInt(self, "Taille de la scène", "Hauteur:", self.scene_model.scene_height, 1)
            if ok2:
                self.scene_model.scene_width = width
                self.scene_model.scene_height = height
                self.scene.setSceneRect(0, 0, width, height)
                self._update_scene_visuals()
                self._update_background()
                self._update_zoom_status() # Update zoom status after scene size change

    def set_background(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Charger une image d'arrière-plan", "", "Images (*.png *.jpg *.jpeg)")
        if filePath:
            self.scene_model.background_path = filePath
            self._update_background()

    def _update_background(self):
        if self.background_item:
            self.scene.removeItem(self.background_item)
            self.background_item = None
        
        if self.scene_model.background_path:
            pixmap = QPixmap(self.scene_model.background_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(self.scene.sceneRect().size().toSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.background_item = QGraphicsPixmapItem(scaled_pixmap)
                scene_rect = self.scene.sceneRect()
                bg_rect = self.background_item.boundingRect()
                self.background_item.setPos(scene_rect.center().x() - bg_rect.width()/2, scene_rect.center().y() - bg_rect.height()/2)
                self.background_item.setZValue(-10000)
                self.scene.addItem(self.background_item)

    def toggle_rotation_handles(self, visible):
        for item in self.graphics_items.values():
            if isinstance(item, PuppetPiece):
                item.set_handle_visibility(visible)

    def save_scene(self):
        filePath, _ = QFileDialog.getSaveFileName(self, "Sauvegarder la scène", "", "JSON Files (*.json)")
        if filePath:
            self.export_scene(filePath)

    def load_scene(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Charger une scène", "", "JSON Files (*.json)")
        if filePath:
            self.import_scene(filePath)

    def play_animation(self):
        self.playback_timer.start()

    def pause_animation(self):
        self.playback_timer.stop()

    def next_frame(self):
        current_frame = self.scene_model.current_frame
        start_frame = self.scene_model.start_frame
        end_frame = self.scene_model.end_frame
        new_frame = current_frame + 1
        if new_frame > end_frame:
            new_frame = start_frame
        self.timeline_widget.set_current_frame(new_frame)

    def set_fps(self, fps):
        self.scene_model.fps = fps
        self.playback_timer.setInterval(1000 // fps if fps > 0 else 0)

    def set_range(self, start, end):
        self.scene_model.start_frame = start
        self.scene_model.end_frame = end

    def _update_timeline_ui_from_model(self):
        self.timeline_widget.fps_spinbox.setValue(self.scene_model.fps)
        self.timeline_widget.start_frame_spinbox.setValue(self.scene_model.start_frame)
        self.timeline_widget.end_frame_spinbox.setValue(self.scene_model.end_frame)
        self.timeline_widget.slider.setRange(self.scene_model.start_frame, self.scene_model.end_frame)

    def add_puppet(self, file_path, puppet_name):
        puppet = Puppet()
        loader = SvgLoader(file_path)
        renderer = loader.renderer
        self.renderers[puppet_name] = renderer
        puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)
        self.scene_model.add_puppet(puppet_name, puppet)
        self.puppet_scales[puppet_name] = 1.0
        self.puppet_paths[puppet_name] = file_path
        self._add_puppet_graphics(puppet_name, puppet, file_path, renderer, loader)
        if hasattr(self, "inspector_widget"):
            self.inspector_widget.refresh()

    def _add_puppet_graphics(self, puppet_name, puppet, file_path, renderer, loader):
        pieces = {}
        for name, member in puppet.members.items():
            offset_x, offset_y = loader.get_group_offset(name) or (0, 0)
            pivot_x = member.pivot[0] - offset_x
            pivot_y = member.pivot[1] - offset_y
            piece = PuppetPiece(file_path, name, pivot_x, pivot_y, renderer)
            piece.setZValue(member.z_order)
            pieces[name] = piece
            self.graphics_items[f"{puppet_name}:{name}"] = piece

        scene_center = self.scene.sceneRect().center()
        for name, piece in pieces.items():
            member = puppet.members[name]
            if member.parent:
                parent_piece = pieces[member.parent.name]
                piece.set_parent_piece(parent_piece, member.rel_pos[0], member.rel_pos[1])
            else: # Root piece
                offset_x, offset_y = loader.get_group_offset(name) or (0, 0)
                pivot_x_local = member.pivot[0] - offset_x
                pivot_y_local = member.pivot[1] - offset_y
                final_x = scene_center.x() - pivot_x_local
                final_y = scene_center.y() - pivot_y_local
                piece.setPos(final_x, final_y)
                piece.setFlag(QGraphicsItem.ItemIsMovable, True)
                piece.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        for piece in pieces.values():
            self.scene.addItem(piece)
            self.scene.addItem(piece.pivot_handle)
            if piece.rotation_handle:
                self.scene.addItem(piece.rotation_handle)

        for piece in pieces.values():
            if piece.parent_piece:
                piece.update_transform_from_parent()
            else:
                piece.update_handle_positions()

    def update_scene_from_model(self):
        index = self.scene_model.current_frame
        keyframes = self.scene_model.keyframes
        if not keyframes:
            return

        prev_kf_index = -1
        next_kf_index = -1
        sorted_indices = sorted(keyframes.keys())
        for i in sorted_indices:
            if i <= index:
                prev_kf_index = i
            if i > index:
                next_kf_index = i
                break

        if prev_kf_index != -1 and next_kf_index != -1 and prev_kf_index != next_kf_index:
            prev_kf = keyframes[prev_kf_index]
            next_kf = keyframes[next_kf_index]
            ratio = (index - prev_kf_index) / (next_kf_index - prev_kf_index)
            for puppet_name, puppet in self.scene_model.puppets.items():
                prev_pose = prev_kf.puppets.get(puppet_name, {})
                next_pose = next_kf.puppets.get(puppet_name, {})
                for member_name in puppet.members:
                    prev_state = prev_pose.get(member_name)
                    next_state = next_pose.get(member_name)
                    if not prev_state or not next_state:
                        continue
                    prev_rot = prev_state['rotation']
                    next_rot = next_state['rotation']
                    interp_rot = prev_rot + (next_rot - prev_rot) * ratio
                    piece = self.graphics_items[f"{puppet_name}:{member_name}"]
                    piece.local_rotation = interp_rot
                    if not piece.parent_piece:
                        prev_pos = prev_state['pos']
                        next_pos = next_state['pos']
                        interp_x = prev_pos[0] + (next_pos[0] - prev_pos[0]) * ratio
                        interp_y = prev_pos[1] + (next_pos[1] - prev_pos[1]) * ratio
                        piece.setPos(interp_x, interp_y)
        else:
            target_kf_index = prev_kf_index if prev_kf_index != -1 else next_kf_index
            if target_kf_index == -1:
                return
            kf = keyframes[target_kf_index]
            for puppet_name, puppet_state in kf.puppets.items():
                for member_name, member_state in puppet_state.items():
                    piece = self.graphics_items[f"{puppet_name}:{member_name}"]
                    piece.local_rotation = member_state['rotation']
                    if not piece.parent_piece:
                        pos = member_state['pos']
                        piece.setPos(pos[0], pos[1])

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

    def delete_keyframe(self, frame_index):
        self.scene_model.remove_keyframe(frame_index)
        self.timeline_widget.remove_keyframe_marker(frame_index)

    def go_to_frame(self, index):
        self.scene_model.go_to_frame(index)
        self.timeline_widget.set_current_frame(index)
        self.update_scene_from_model()

    def export_scene(self, file_path):
        self.scene_model.export_json(file_path)

    def import_scene(self, file_path):
        self.scene_model.import_json(file_path)
        self.timeline_widget.clear_keyframes()
        for kf_index in self.scene_model.keyframes:
            self.timeline_widget.add_keyframe_marker(kf_index)
        self._update_timeline_ui_from_model()
        self.scene.setSceneRect(0, 0, self.scene_model.scene_width, self.scene_model.scene_height)
        self._update_background()
        self.update_scene_from_model()

    # -------------------------------------------------
    # Inspector actions
    # -------------------------------------------------
    def scale_puppet(self, puppet_name, ratio):
        puppet = self.scene_model.puppets.get(puppet_name)
        if not puppet:
            return
        for member_name in puppet.members:
            key = f"{puppet_name}:{member_name}"
            piece = self.graphics_items.get(key)
            if not piece:
                continue
            piece.setScale(piece.scale() * ratio)
            if piece.parent_piece:
                rel_x, rel_y = piece.rel_to_parent
                piece.rel_to_parent = (rel_x * ratio, rel_y * ratio)
        for root_member in puppet.get_root_members():
            root_piece = self.graphics_items.get(f"{puppet_name}:{root_member.name}")
            if not root_piece:
                continue
            for child in root_piece.children:
                child.update_transform_from_parent()

    def delete_puppet(self, puppet_name):
        puppet = self.scene_model.puppets.get(puppet_name)
        if not puppet:
            return
        for member_name in list(puppet.members.keys()):
            key = f"{puppet_name}:{member_name}"
            piece = self.graphics_items.pop(key, None)
            if piece:
                self.scene.removeItem(piece)
                self.scene.removeItem(piece.pivot_handle)
                if piece.rotation_handle:
                    self.scene.removeItem(piece.rotation_handle)
        self.scene_model.remove_puppet(puppet_name)
        self.puppet_scales.pop(puppet_name, None)
        self.puppet_paths.pop(puppet_name, None)

    def duplicate_puppet(self, puppet_name):
        path = self.puppet_paths.get(puppet_name)
        if not path:
            return
        base = puppet_name
        i = 1
        while True:
            new_name = f"{base}_{i}"
            if new_name not in self.scene_model.puppets:
                break
            i += 1
        self.add_puppet(path, new_name)
        scale = self.puppet_scales.get(puppet_name, 1.0)
        if scale != 1.0:
            self.puppet_scales[new_name] = scale
            self.scale_puppet(new_name, scale)

    def delete_object(self, name):
        item = self.graphics_items.pop(name, None)
        if item:
            self.scene.removeItem(item)
        self.scene_model.remove_object(name)

    def duplicate_object(self, name):
        obj = self.scene_model.objects.get(name)
        if not obj:
            return
        base = name
        i = 1
        while True:
            new_name = f"{base}_{i}"
            if new_name not in self.scene_model.objects:
                break
            i += 1
        new_obj = SceneObject(new_name, obj.obj_type, obj.file_path,
                               x=obj.x + 10, y=obj.y + 10,
                               rotation=obj.rotation, scale=obj.scale)
        self.scene_model.add_object(new_obj)
        self._add_object_graphics(new_obj)

    def _add_object_graphics(self, scene_object: SceneObject):
        if scene_object.obj_type == "image":
            pix = QPixmap(scene_object.file_path)
            item = QGraphicsPixmapItem(pix)
        elif scene_object.obj_type == "svg":
            item = QGraphicsSvgItem(scene_object.file_path)
        else:
            return
        item.setPos(scene_object.x, scene_object.y)
        item.setRotation(scene_object.rotation)
        item.setScale(scene_object.scale)
        item.setFlag(QGraphicsItem.ItemIsMovable, True)
        item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.scene.addItem(item)
        self.graphics_items[scene_object.name] = item
