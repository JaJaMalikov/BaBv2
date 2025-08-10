from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow,
    QGraphicsScene,
    QVBoxLayout,
    QWidget,
    QGraphicsPixmapItem,
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QToolButton,
    QFrame,
    QStyle,
    QHBoxLayout,
)
from PySide6.QtGui import QPainter, QPixmap, QAction, QColor, QPen
from PySide6.QtCore import Qt, QTimer, QPointF, QSize

from core.scene_model import SceneModel, SceneObject
from core.puppet_piece import PuppetPiece
from ui.timeline_widget import TimelineWidget
from ui.inspector_widget import InspectorWidget
from ui.library_widget import LibraryWidget
from ui.zoomable_view import ZoomableView
from ui.playback_handler import PlaybackHandler
from ui.object_manager import ObjectManager
from ui.draggable_widget import DraggableOverlay
import ui.scene_io as scene_io
from ui.icons import (
    icon_scene_size, icon_background, icon_library, icon_inspector, icon_timeline,
    icon_chevron_left, icon_chevron_right
)
from ui.styles import BUTTON_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Borne and the Bayrou - Disco MIX")

        self.scene_model = SceneModel()
        self.background_item = None
        self.zoom_factor = 1.0
        self._suspend_item_updates = False

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.scene_model.scene_width, self.scene_model.scene_height)
        
        self.object_manager = ObjectManager(self)

        self.view = ZoomableView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setBackgroundBrush(QColor("#121212"))
        self.view.setFrameShape(QFrame.NoFrame)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view)
        self.setCentralWidget(main_widget)

        self.timeline_dock = QDockWidget("Timeline", self)
        self.timeline_dock.setObjectName("dock_timeline")
        self.timeline_widget = TimelineWidget()
        self.timeline_dock.setWidget(self.timeline_widget)
        self.timeline_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.timeline_dock)

        self.inspector_dock = QDockWidget("Inspector", self)
        self.inspector_dock.setObjectName("dock_inspector")
        self.inspector_widget = InspectorWidget(self)
        self.inspector_dock.setWidget(self.inspector_widget)
        self.inspector_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.inspector_dock)
        self.inspector_dock.hide()

        self.library_dock = QDockWidget("Bibliothèques", self)
        self.library_dock.setObjectName("dock_library")
        self.library_widget = LibraryWidget(root_dir=str(Path.cwd()))
        self.library_dock.setWidget(self.library_widget)
        self.library_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.library_dock)

        self.playback_handler = PlaybackHandler(self.scene_model, self.timeline_widget, self.inspector_widget, self)

        self._create_actions()
        self._build_main_tools_overlay()
        self.connect_signals()
        self._setup_scene_visuals()
        self._apply_unified_stylesheet()

        # --- Startup Sequence ---
        self.showMaximized()
        self.inspector_dock.show()
        self.library_dock.show()
        self.timeline_dock.show()
        self.timeline_dock.visibilityChanged.connect(lambda _: self.ensure_fit())
        self.timeline_dock.topLevelChanged.connect(lambda _: self.ensure_fit())
        self.ensure_fit()
        scene_io.create_blank_scene(self)
        self.ensure_fit()
        self.scene.selectionChanged.connect(self._on_scene_selection_changed)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.fit_to_view)
        QTimer.singleShot(50, self.fit_to_view)

    def _create_actions(self):
        style = self.style()
        self.save_action = QAction(style.standardIcon(QStyle.SP_DialogSaveButton), "Sauvegarder (Ctrl+S)", self)
        self.save_action.setShortcut("Ctrl+S")
        self.load_action = QAction(style.standardIcon(QStyle.SP_DialogOpenButton), "Charger (Ctrl+O)", self)
        self.load_action.setShortcut("Ctrl+O")
        self.scene_size_action = QAction(icon_scene_size(), "Taille Scène", self)
        self.background_action = QAction(icon_background(), "Image de fond", self)

        self.library_dock.toggleViewAction().setIcon(icon_library())
        self.inspector_dock.toggleViewAction().setIcon(icon_inspector())
        self.timeline_dock.toggleViewAction().setIcon(icon_timeline())

    def connect_signals(self):
        # Scene I/O
        self.save_action.triggered.connect(lambda: scene_io.save_scene(self))
        self.load_action.triggered.connect(lambda: scene_io.load_scene(self))
        
        # Scene settings
        self.scene_size_action.triggered.connect(self.set_scene_size)
        self.background_action.triggered.connect(self.set_background)

        # ZoomableView signals
        self.view.zoom_requested.connect(self.zoom)
        self.view.fit_requested.connect(self.fit_to_view)
        self.view.handles_toggled.connect(self.toggle_rotation_handles)
        self.view.item_dropped.connect(self.object_manager.handle_library_drop)

        # PlaybackHandler signals
        self.playback_handler.frame_update_requested.connect(self.update_scene_from_model)
        self.playback_handler.keyframe_add_requested.connect(self.add_keyframe)

        # Library signals
        self.library_widget.addRequested.connect(self.object_manager._add_library_item_to_scene)

    def _build_main_tools_overlay(self):
        self._main_tools_overlay = DraggableOverlay(self.view)
        
        self.main_tools_layout = QHBoxLayout(self._main_tools_overlay)
        self.main_tools_layout.setContentsMargins(4, 4, 4, 4)
        self.main_tools_layout.setSpacing(2)

        icon_size = 32
        button_size = 36

        def make_btn(action: QAction, checkable=False):
            btn = QToolButton(self._main_tools_overlay)
            btn.setDefaultAction(action)
            btn.setIconSize(QSize(icon_size, icon_size))
            btn.setCheckable(checkable)
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setFixedSize(button_size, button_size)
            btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            btn.setAutoRaise(True)
            return btn

        collapse_btn = make_btn(QAction(icon_chevron_left(), "Replier/Déplier", self), checkable=True)
        collapse_btn.setChecked(True)
        
        # Build buttons from actions
        save_btn = make_btn(self.save_action)
        load_btn = make_btn(self.load_action)
        scene_size_btn = make_btn(self.scene_size_action)
        background_btn = make_btn(self.background_action)
        
        library_toggle_btn = make_btn(self.library_dock.toggleViewAction(), checkable=True)
        inspector_toggle_btn = make_btn(self.inspector_dock.toggleViewAction(), checkable=True)
        timeline_toggle_btn = make_btn(self.timeline_dock.toggleViewAction(), checkable=True)

        # Set initial checked state for dock toggles
        library_toggle_btn.setChecked(self.library_dock.isVisible())
        inspector_toggle_btn.setChecked(self.inspector_dock.isVisible())
        timeline_toggle_btn.setChecked(self.timeline_dock.isVisible())

        # Connect dock visibility changes to button checked state
        self.library_dock.visibilityChanged.connect(library_toggle_btn.setChecked)
        self.inspector_dock.visibilityChanged.connect(inspector_toggle_btn.setChecked)
        self.timeline_dock.visibilityChanged.connect(timeline_toggle_btn.setChecked)

        self.main_tool_buttons = [save_btn, load_btn, scene_size_btn, background_btn, 
                    library_toggle_btn, inspector_toggle_btn, timeline_toggle_btn]

        def toggle_main_tools_collapse(checked):
            icon = icon_chevron_left() if checked else icon_chevron_right()
            collapse_btn.setIcon(icon)
            for w in self.main_tool_buttons:
                w.setVisible(checked)
            self._main_tools_overlay.adjustSize()

        collapse_btn.toggled.connect(toggle_main_tools_collapse)

        self.main_tools_layout.addWidget(collapse_btn)
        for w in self.main_tool_buttons:
            self.main_tools_layout.addWidget(w)

        self._main_tools_overlay.move(10, 60)

    def _apply_unified_stylesheet(self):
        self.setStyleSheet(
            """QDockWidget { titlebar-close-icon: none; titlebar-normal-icon: none; background: #1E1E1E; color: #E0E0E0; }
               QDockWidget::title { background: #1B1B1B; padding: 4px 8px; border: 1px solid #2A2A2A; color: #E0E0E0; }
               QStatusBar { background: #121212; color: #CFCFCF; }""")

    def _setup_scene_visuals(self):
        self.scene_border_item = QGraphicsRectItem(); self.scene_size_text_item = QGraphicsTextItem()
        self.scene.addItem(self.scene_border_item); self.scene.addItem(self.scene_size_text_item)
        self._update_scene_visuals()

    def _update_scene_visuals(self):
        rect = self.scene.sceneRect()
        self.scene_border_item.setPen(QPen(QColor(100, 100, 100), 2, Qt.DashLine)); self.scene_border_item.setRect(rect)
        text = f"{self.scene_model.scene_width}x{self.scene_model.scene_height}"
        self.scene_size_text_item.setPlainText(text); self.scene_size_text_item.setDefaultTextColor(QColor(150, 150, 150))
        text_rect = self.scene_size_text_item.boundingRect()
        self.scene_size_text_item.setPos(rect.right() - text_rect.width() - 10, rect.bottom() - text_rect.height() - 10)

    def _update_zoom_status(self):
        txt = f"Zoom: {self.zoom_factor:.0%}"
        self.statusBar().showMessage(txt)
        if hasattr(self.view, 'set_zoom_label'): self.view.set_zoom_label(f"{int(self.zoom_factor*100)}%")

    def zoom(self, factor):
        self.view.scale(factor, factor)
        self.zoom_factor *= factor
        self._update_zoom_status()

    def fit_to_view(self):
        self.view.resetTransform()
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.zoom_factor = self.view.transform().m11()
        self._update_zoom_status()

    def ensure_fit(self):
        QTimer.singleShot(0, self.fit_to_view)

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
                self._update_zoom_status()

    def set_background(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Charger une image d'arrière-plan", "", "Images (*.png *.jpg *.jpeg)")
        if filePath:
            self.scene_model.background_path = filePath
            self._update_background()

    def _update_background(self):
        if self.background_item:
            self.scene.removeItem(self.background_item)
            self.background_item = None
        if self.scene_model.background_path and Path(self.scene_model.background_path).exists():
            pixmap = QPixmap(self.scene_model.background_path)
            scaled_pixmap = pixmap.scaled(self.scene.sceneRect().size().toSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.background_item = QGraphicsPixmapItem(scaled_pixmap)
            scene_rect = self.scene.sceneRect()
            self.background_item.setPos(scene_rect.center() - self.background_item.boundingRect().center())
            self.background_item.setZValue(-10000)
            self.scene.addItem(self.background_item)

    def toggle_rotation_handles(self, visible):
        for item in self.object_manager.graphics_items.values():
            if isinstance(item, PuppetPiece):
                item.set_handle_visibility(visible)
        self.view.handles_btn.setChecked(visible)

    def update_scene_from_model(self):
        index = self.scene_model.current_frame
        keyframes = self.scene_model.keyframes
        if not keyframes: return

        graphics_items = self.object_manager.graphics_items

        sorted_indices = sorted(keyframes.keys())
        prev_kf_index = next((i for i in reversed(sorted_indices) if i <= index), -1)
        next_kf_index = next((i for i in sorted_indices if i > index), -1)

        if prev_kf_index != -1 and next_kf_index != -1 and prev_kf_index != next_kf_index:
            prev_kf, next_kf = keyframes[prev_kf_index], keyframes[next_kf_index]
            ratio = (index - prev_kf_index) / (next_kf_index - prev_kf_index)
            for name, puppet in self.scene_model.puppets.items():
                prev_pose, next_pose = prev_kf.puppets.get(name, {}), next_kf.puppets.get(name, {})
                for member_name in puppet.members:
                    if not (prev_state := prev_pose.get(member_name)) or not (next_state := next_pose.get(member_name)): continue
                    interp_rot = prev_state['rotation'] + (next_state['rotation'] - prev_state['rotation']) * ratio
                    piece = graphics_items[f"{name}:{member_name}"]
                    piece.local_rotation = interp_rot
                    if not piece.parent_piece:
                        prev_pos, next_pos = prev_state['pos'], next_state['pos']
                        interp_x = prev_pos[0] + (next_pos[0] - prev_pos[0]) * ratio
                        interp_y = prev_pos[1] + (next_pos[1] - prev_pos[1]) * ratio
                        piece.setPos(interp_x, interp_y)
        else:
            target_kf_index = prev_kf_index if prev_kf_index != -1 else next_kf_index
            if target_kf_index == -1: return
            kf = keyframes[target_kf_index]
            for name, state in kf.puppets.items():
                for member, member_state in state.items():
                    piece = graphics_items[f"{name}:{member}"]
                    piece.local_rotation = member_state['rotation']
                    if not piece.parent_piece: piece.setPos(*member_state['pos'])

        for name, puppet in self.scene_model.puppets.items():
            for root_member in puppet.get_root_members():
                root_piece = graphics_items[f"{name}:{root_member.name}"]
                root_piece.setRotation(root_piece.local_rotation)
                for child in root_piece.children:
                    child.update_transform_from_parent()

        def state_for(name: str):
            si = sorted(keyframes.keys())
            prev = next((i for i in reversed(si) if i <= index and name in keyframes[i].objects), None)
            if prev is None: return None
            return keyframes[prev].objects.get(name)

        self._suspend_item_updates = True
        try:
            for name, base_obj in self.scene_model.objects.items():
                st = state_for(name)
                gi = graphics_items.get(name)
                if st is None:
                    if gi:
                        gi.setSelected(False)
                        gi.setVisible(False)
                    continue
                if gi is None:
                    tmp = SceneObject(name, st.get('obj_type', base_obj.obj_type), st.get('file_path', base_obj.file_path),
                                      x=st.get('x', base_obj.x), y=st.get('y', base_obj.y), rotation=st.get('rotation', base_obj.rotation),
                                      scale=st.get('scale', base_obj.scale), z=st.get('z', getattr(base_obj, 'z', 0)))
                    self.object_manager._add_object_graphics(tmp)
                    gi = graphics_items.get(name)
                if gi:
                    gi.setVisible(True)
                    gi.setPos(st.get('x', gi.x()), st.get('y', gi.y()))
                    gi.setRotation(st.get('rotation', gi.rotation()))
                    gi.setScale(st.get('scale', gi.scale()))
                    gi.setZValue(st.get('z', int(gi.zValue())))
                    attached = st.get('attached_to', None)
                    if attached:
                        try:
                            puppet_name, member_name = attached
                            parent_piece = graphics_items.get(f"{puppet_name}:{member_name}")
                            if parent_piece and gi.parentItem() is not parent_piece:
                                scene_pt = gi.mapToScene(gi.transformOriginPoint())
                                gi.setParentItem(parent_piece)
                                local_pt = parent_piece.mapFromScene(scene_pt)
                                gi.setPos(local_pt - gi.transformOriginPoint())
                        except Exception:
                            pass
                    else:
                        if gi.parentItem() is not None:
                            scene_pt = gi.mapToScene(gi.transformOriginPoint())
                            gi.setParentItem(None)
                            gi.setPos(scene_pt - gi.transformOriginPoint())
        finally:
            self._suspend_item_updates = False

    def add_keyframe(self, frame_index):
        states = self.object_manager.capture_puppet_states()
        self.scene_model.add_keyframe(frame_index, states)
        self.timeline_widget.add_keyframe_marker(frame_index)

    def select_object_in_inspector(self, name: str):
        if not hasattr(self, 'inspector_widget') or not self.inspector_widget:
            return
        lw = self.inspector_widget.list_widget
        for i in range(lw.count()):
            it = lw.item(i)
            typ, nm = it.data(Qt.UserRole)
            if typ == 'object' and nm == name:
                lw.setCurrentItem(it)
                break

    def _on_scene_selection_changed(self):
        for item in self.scene.selectedItems():
            for name, gi in self.object_manager.graphics_items.items():
                if gi is item and name in self.scene_model.objects:
                    self.select_object_in_inspector(name)
                    return
