import os
import json
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
    QGraphicsTextItem,
    QToolBar,
    QToolButton,
    QLabel,
    QHBoxLayout,
    QFrame,
)
from PySide6.QtGui import QPainter, QPixmap, QAction, QColor, QPen, QIcon
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
    def __init__(self, scene, main_window, parent=None):
        super().__init__(scene, parent)
        self.main_window = main_window
        self._overlay = None
        self._zoom_label = None
        self._build_overlay()

    def _build_overlay(self):
        self._overlay = QWidget(self)
        self._overlay.setAttribute(Qt.WA_StyledBackground, True)
        self._overlay.setStyleSheet("background: rgba(0,0,0,120); border-radius: 8px;")
        lay = QHBoxLayout(self._overlay)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(6)

        def make_btn(icon: QIcon | None, tooltip, cb):
            btn = QToolButton(self._overlay)
            if icon: btn.setIcon(icon)
            btn.setToolTip(tooltip)
            btn.clicked.connect(cb)
            btn.setStyleSheet("QToolButton { color: #E0E0E0; font-weight: 500; }")
            btn.setAutoRaise(True)
            return btn

        minus_btn = make_btn(self._icon_minus(), "Zoom arrière (Ctrl+Molette)", lambda: self.main_window.zoom(0.8))
        plus_btn = make_btn(self._icon_plus(), "Zoom avant (Ctrl+Molette)", lambda: self.main_window.zoom(1.25))
        fit_btn = make_btn(self._icon_fit(), "Ajuster à la scène", self.main_window.fit_to_view)
        ctr_btn = make_btn(self._icon_center(), "Centrer sur la marionnette", self.main_window.center_on_puppet)
        self.handles_btn = QToolButton(self._overlay)
        self.handles_btn.setIcon(self._icon_rotate())
        self.handles_btn.setToolTip("Afficher/Masquer les poignées de rotation")
        self.handles_btn.setCheckable(True)
        self.handles_btn.setChecked(False)
        self.handles_btn.toggled.connect(self.main_window.toggle_rotation_handles)
        self.handles_btn.setStyleSheet("QToolButton { color: #E0E0E0; font-weight: 500; }")
        self.handles_btn.setAutoRaise(True)

        self._zoom_label = QLabel("100%", self._overlay)
        self._zoom_label.setStyleSheet("color: #CFCFCF; padding-left: 6px; padding-right: 2px;")

        for w in (minus_btn, plus_btn, fit_btn, ctr_btn, self.handles_btn, self._zoom_label):
            lay.addWidget(w)

        self._position_overlay()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_overlay()

    def _position_overlay(self):
        if not self._overlay: return
        margin = 10
        self._overlay.setGeometry(margin, margin, self._overlay.sizeHint().width(), self._overlay.sizeHint().height())

    def set_zoom_label(self, text: str):
        if self._zoom_label: self._zoom_label.setText(text)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
            if self.main_window: self.main_window.zoom(factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_panning", False):
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            h, v = self.horizontalScrollBar(), self.verticalScrollBar()
            h.setValue(h.value() - int(delta.x()))
            v.setValue(v.value() - int(delta.y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and getattr(self, "_panning", False):
            self._panning = False
            self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _make_icon(self, draw_fn, size: int = 20) -> QIcon:
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor('#E0E0E0'), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        draw_fn(p, size)
        p.end()
        return QIcon(pm)

    def _icon_plus(self): return self._make_icon(lambda p, s: (p.drawLine(int(s/2-s*0.35), s//2, int(s/2+s*0.35), s//2), p.drawLine(s//2, int(s/2-s*0.35), s//2, int(s/2+s*0.35))))
    def _icon_minus(self): return self._make_icon(lambda p, s: p.drawLine(int(s/2-s*0.35), s//2, int(s/2+s*0.35), s//2))
    def _icon_center(self): return self._make_icon(lambda p, s: (p.drawEllipse(int(s/2-s*0.175), int(s/2-s*0.175), int(s*0.35), int(s*0.35)), p.drawLine(int(s*0.15), s//2, int(s*0.85), s//2), p.drawLine(s//2, int(s*0.15), s//2, int(s*0.85))))
    def _icon_fit(self): return self._make_icon(lambda p, s: (p.drawLine(4, 10, 4, 4), p.drawLine(4, 4, 10, 4), p.drawLine(s-10, 4, s-4, 4), p.drawLine(s-4, 4, s-4, 10), p.drawLine(s-4, s-10, s-4, s-4), p.drawLine(s-4, s-4, s-10, s-4), p.drawLine(10, s-4, 4, s-4), p.drawLine(4, s-4, 4, s-10)))
    def _icon_rotate(self): return self._make_icon(lambda p, s: (p.drawArc(int(s*0.18), int(s*0.18), int(s*0.64), int(s*0.64), 45*16, 270*16), p.drawLine(int(s*0.5), int(s*0.18), int(s*0.5-s*0.15), int(s*0.18+s*0.15)), p.drawLine(int(s*0.5), int(s*0.18), int(s*0.5+s*0.15), int(s*0.18+s*0.15))))

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
        self.zoom_factor = 1.0

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.scene_model.scene_width, self.scene_model.scene_height)
        
        self.view = ZoomableView(self.scene, self, self)
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

        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.next_frame)
        self.set_fps(self.scene_model.fps)

        self.setup_menus()
        self.connect_signals()
        self._setup_scene_visuals()
        self._build_main_toolbar()
        self._apply_unified_stylesheet()

        # --- Startup Sequence ---
        self.showMaximized()
        self.import_scene("demo.json")

    def setup_menus(self):
        self.ui.menuToggle_Inspector.clear(); self.ui.menuToggle_Inspector.addAction(self.inspector_dock.toggleViewAction())
        self.ui.menuToggle_Timeline.clear(); self.ui.menuToggle_Timeline.addAction(self.timeline_dock.toggleViewAction())
        self.ui.menuToggle_Transformation.clear()
        toggle_handles_action = QAction("Afficher les poignées", self, checkable=True); toggle_handles_action.setChecked(False); toggle_handles_action.toggled.connect(self.toggle_rotation_handles)
        self.ui.menuToggle_Transformation.addAction(toggle_handles_action)

        self.ui.action_9.setShortcut("Ctrl+="); self.ui.action_9.setStatusTip("Zoom avant")
        self.ui.action_10.setShortcut("Ctrl+-"); self.ui.action_10.setStatusTip("Zoom arrière")
        self.ui.actionFit.setShortcut("F"); self.ui.actionFit.setStatusTip("Adapter la scène à la vue")
        self.ui.actionCenter.setShortcut("C"); self.ui.actionCenter.setStatusTip("Centrer sur la marionnette")
        self.inspector_dock.toggleViewAction().setShortcut("F4")
        self.timeline_dock.toggleViewAction().setShortcut("F3")

    def connect_signals(self):
        self.timeline_widget.addKeyframeClicked.connect(self.add_keyframe)
        self.timeline_widget.deleteKeyframeClicked.connect(self.delete_keyframe)
        self.timeline_widget.frameChanged.connect(self.go_to_frame)
        self.timeline_widget.playClicked.connect(self.play_animation)
        self.timeline_widget.pauseClicked.connect(self.pause_animation)
        self.timeline_widget.stopClicked.connect(self.stop_animation)
        self.timeline_widget.loopToggled.connect(self._on_loop_toggled)
        self.timeline_widget.fpsChanged.connect(self.set_fps)
        self.timeline_widget.rangeChanged.connect(self.set_range)

        self.ui.actionSauvegarder.triggered.connect(self.save_scene)
        self.ui.actionCharger_2.triggered.connect(self.load_scene)
        self.ui.actionTaille_Sc_ne.triggered.connect(self.set_scene_size)
        self.ui.actionBackground.triggered.connect(self.set_background)

        self.ui.action_9.triggered.connect(lambda: self.zoom(1.25))
        self.ui.action_10.triggered.connect(lambda: self.zoom(0.8))
        self.ui.actionFit.triggered.connect(self.fit_to_view)
        self.ui.actionCenter.triggered.connect(self.center_on_puppet)

    def _build_main_toolbar(self):
        tb = QToolBar("Outils", self); tb.setObjectName("toolbar_main"); tb.setMovable(False); tb.setFloatable(False)
        tb.setToolButtonStyle(Qt.ToolButtonIconOnly); tb.setIconSize(tb.iconSize())
        self.ui.action_9.setIcon(self.view._icon_plus()); self.ui.action_10.setIcon(self.view._icon_minus())
        self.ui.actionFit.setIcon(self.view._icon_fit()); self.ui.actionCenter.setIcon(self.view._icon_center())
        for action in [self.ui.action_9, self.ui.action_10, self.ui.actionFit, self.ui.actionCenter]: tb.addAction(action)
        tb.addSeparator()
        tb.addAction(self.inspector_dock.toggleViewAction()); tb.addAction(self.timeline_dock.toggleViewAction())
        self.addToolBar(Qt.TopToolBarArea, tb)

    def _apply_unified_stylesheet(self):
        self.setStyleSheet(
            """QDockWidget { titlebar-close-icon: none; titlebar-normal-icon: none; background: #1E1E1E; color: #E0E0E0; }
               QDockWidget::title { background: #1B1B1B; padding: 4px 8px; border: 1px solid #2A2A2A; color: #E0E0E0; }
               QToolBar { background: #1B1B1B; border-bottom: 1px solid #2A2A2A; spacing: 4px; }
               QToolButton { color: #E0E0E0; }
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

    def zoom(self, factor): self.view.scale(factor, factor); self.zoom_factor *= factor; self._update_zoom_status()
    def fit_to_view(self): self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio); self.zoom_factor = self.view.transform().m11(); self._update_zoom_status()
    def center_on_puppet(self): 
        if (puppet_root := self.graphics_items.get("manu:torse")): self.view.centerOn(puppet_root)

    def set_scene_size(self):
        width, ok1 = QInputDialog.getInt(self, "Taille de la scène", "Largeur:", self.scene_model.scene_width, 1)
        if ok1:
            height, ok2 = QInputDialog.getInt(self, "Taille de la scène", "Hauteur:", self.scene_model.scene_height, 1)
            if ok2:
                self.scene_model.scene_width = width; self.scene_model.scene_height = height
                self.scene.setSceneRect(0, 0, width, height)
                self._update_scene_visuals(); self._update_background(); self._update_zoom_status()

    def set_background(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Charger une image d'arrière-plan", "", "Images (*.png *.jpg *.jpeg)")
        if filePath: self.scene_model.background_path = filePath; self._update_background()

    def _update_background(self):
        if self.background_item: self.scene.removeItem(self.background_item); self.background_item = None
        if self.scene_model.background_path and os.path.exists(self.scene_model.background_path):
            pixmap = QPixmap(self.scene_model.background_path)
            scaled_pixmap = pixmap.scaled(self.scene.sceneRect().size().toSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.background_item = QGraphicsPixmapItem(scaled_pixmap)
            scene_rect = self.scene.sceneRect()
            self.background_item.setPos(scene_rect.center() - self.background_item.boundingRect().center())
            self.background_item.setZValue(-10000)
            self.scene.addItem(self.background_item)

    def toggle_rotation_handles(self, visible):
        for item in self.graphics_items.values():
            if isinstance(item, PuppetPiece): item.set_handle_visibility(visible)

    def save_scene(self):
        filePath, _ = QFileDialog.getSaveFileName(self, "Sauvegarder la scène", "", "JSON Files (*.json)")
        if filePath: self.export_scene(filePath)

    def load_scene(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Charger une scène", "", "JSON Files (*.json)")
        if filePath: self.import_scene(filePath)

    def play_animation(self): self.playback_timer.start()
    def pause_animation(self): self.playback_timer.stop()
    def stop_animation(self):
        self.playback_timer.stop()
        self.timeline_widget.set_current_frame(self.scene_model.start_frame)

    def next_frame(self):
        current = self.scene_model.current_frame
        start, end = self.scene_model.start_frame, self.scene_model.end_frame
        new_frame = current + 1
        if new_frame > end:
            if self.timeline_widget.loop_enabled:
                new_frame = start
            else:
                self.pause_animation()
                self.timeline_widget.play_btn.setChecked(False)
                return
        self.timeline_widget.set_current_frame(new_frame)

    def _on_loop_toggled(self, enabled: bool): self.timeline_widget.loop_enabled = enabled
    def set_fps(self, fps): self.scene_model.fps = fps; self.playback_timer.setInterval(1000 // fps if fps > 0 else 0)
    def set_range(self, start, end): self.scene_model.start_frame = start; self.scene_model.end_frame = end

    def _update_timeline_ui_from_model(self):
        self.timeline_widget.fps_spinbox.setValue(self.scene_model.fps)
        self.timeline_widget.start_frame_spinbox.setValue(self.scene_model.start_frame)
        self.timeline_widget.end_frame_spinbox.setValue(self.scene_model.end_frame)
        self.timeline_widget.slider.setRange(self.scene_model.start_frame, self.scene_model.end_frame)

    def add_puppet(self, file_path, puppet_name):
        puppet = Puppet(); loader = SvgLoader(file_path); renderer = loader.renderer
        self.renderers[puppet_name] = renderer
        puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)
        self.scene_model.add_puppet(puppet_name, puppet)
        self.puppet_scales[puppet_name] = 1.0
        self.puppet_paths[puppet_name] = file_path
        self._add_puppet_graphics(puppet_name, puppet, file_path, renderer, loader)
        if hasattr(self, "inspector_widget"): self.inspector_widget.refresh()

    def _add_puppet_graphics(self, puppet_name, puppet, file_path, renderer, loader):
        pieces = {}
        for name, member in puppet.members.items():
            offset_x, offset_y = loader.get_group_offset(name) or (0, 0)
            pivot_x, pivot_y = member.pivot[0] - offset_x, member.pivot[1] - offset_y
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
                final_x = scene_center.x() - (member.pivot[0] - offset_x)
                final_y = scene_center.y() - (member.pivot[1] - offset_y)
                piece.setPos(final_x, final_y)
                piece.setFlag(QGraphicsItem.ItemIsMovable, True)
                piece.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        for piece in pieces.values():
            self.scene.addItem(piece); self.scene.addItem(piece.pivot_handle)
            if piece.rotation_handle: self.scene.addItem(piece.rotation_handle)

        for piece in pieces.values():
            if piece.parent_piece: piece.update_transform_from_parent()
            else: piece.update_handle_positions()

    def update_scene_from_model(self):
        index = self.scene_model.current_frame; keyframes = self.scene_model.keyframes
        if not keyframes: return

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
                    piece = self.graphics_items[f"{name}:{member_name}"]
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
                    piece = self.graphics_items[f"{name}:{member}"]
                    piece.local_rotation = member_state['rotation']
                    if not piece.parent_piece: piece.setPos(*member_state['pos'])

        for puppet in self.scene_model.puppets.values():
            for root_member in puppet.get_root_members():
                root_piece = self.graphics_items[f"{next(iter(self.scene_model.puppets.keys()))}:{root_member.name}"]
                root_piece.setRotation(root_piece.local_rotation)
                for child in root_piece.children: child.update_transform_from_parent()

    def add_keyframe(self, frame_index):
        kf = self.scene_model.add_keyframe(frame_index)
        for name, puppet in self.scene_model.puppets.items():
            puppet_state = {}
            for member_name in puppet.members:
                piece = self.graphics_items[f"{name}:{member_name}"]
                puppet_state[member_name] = {'rotation': piece.local_rotation, 'pos': (piece.x(), piece.y())}
            kf.puppets[name] = puppet_state
        self.timeline_widget.add_keyframe_marker(frame_index)

    def delete_keyframe(self, frame_index):
        self.scene_model.remove_keyframe(frame_index)
        self.timeline_widget.remove_keyframe_marker(frame_index)

    def go_to_frame(self, index):
        self.scene_model.go_to_frame(index)
        self.timeline_widget.set_current_frame(index)
        self.update_scene_from_model()

    def export_scene(self, file_path):
        # Ensure the last known state is in a keyframe if there are none
        if not self.scene_model.keyframes:
            self.add_keyframe(0)

        puppets_data = {}
        for name, puppet in self.scene_model.puppets.items():
            root_piece = self.graphics_items.get(f"{name}:{puppet.get_root_members()[0].name}")
            if root_piece:
                puppets_data[name] = {
                    "path": self.puppet_paths.get(name),
                    "scale": self.puppet_scales.get(name, 1.0),
                    "position": [root_piece.x(), root_piece.y()]
                }

        data = {
            "settings": {
                "start_frame": self.scene_model.start_frame,
                "end_frame": self.scene_model.end_frame,
                "fps": self.scene_model.fps,
                "scene_width": self.scene_model.scene_width,
                "scene_height": self.scene_model.scene_height,
                "background_path": self.scene_model.background_path
            },
            "puppets_data": puppets_data,
            "objects": {k: v.__dict__ for k, v in self.scene_model.objects.items()},
            "keyframes": {
                k: {"objects": v.objects, "puppets": v.puppets}
                for k, v in self.scene_model.keyframes.items()
            }
        }
        
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Scene saved to {file_path}")
        except (IOError, TypeError) as e:
            print(f"Error saving scene: {e}")

    def _create_blank_scene(self):
        for name in list(self.scene_model.puppets.keys()): self.delete_puppet(name)
        for name in list(self.scene_model.objects.keys()): self.delete_object(name)
        self.renderers.clear()
        self.graphics_items.clear()
        self.scene_model.keyframes.clear()
        self.timeline_widget.clear_keyframes()
        self.add_puppet("assets/test_genou.svg", "manu")
        self._update_timeline_ui_from_model()
        self.inspector_widget.refresh()

    def import_scene(self, file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Clear existing scene
            for name in list(self.scene_model.puppets.keys()): self.delete_puppet(name)
            for name in list(self.scene_model.objects.keys()): self.delete_object(name)
            self.renderers.clear()
            self.graphics_items.clear()

            # Load settings
            settings = data.get("settings", {})
            self.scene_model.start_frame = settings.get("start_frame", 0)
            self.scene_model.end_frame = settings.get("end_frame", 100)
            self.scene_model.fps = settings.get("fps", 24)
            self.scene_model.scene_width = settings.get("scene_width", 1920)
            self.scene_model.scene_height = settings.get("scene_height", 1080)
            self.scene_model.background_path = settings.get("background_path")

            # Rebuild puppets
            puppets_data = data.get("puppets_data", {})
            for name, p_data in puppets_data.items():
                puppet_path = p_data.get("path")
                if puppet_path and os.path.exists(puppet_path):
                    self.add_puppet(puppet_path, name)
                    scale = p_data.get("scale", 1.0)
                    if scale != 1.0:
                        self.scale_puppet(name, scale)
                        self.puppet_scales[name] = scale
                    
                    pos = p_data.get("position")
                    root_member_name = self.scene_model.puppets[name].get_root_members()[0].name
                    root_piece = self.graphics_items.get(f"{name}:{root_member_name}")
                    if root_piece and pos:
                        root_piece.setPos(pos[0], pos[1])

            # Load keyframes
            self.scene_model.keyframes.clear()
            keyframes_data = data.get("keyframes", {})
            for frame_idx, kf_data in keyframes_data.items():
                kf = self.scene_model.add_keyframe(int(frame_idx))
                kf.puppets = kf_data.get("puppets", {})
                kf.objects = kf_data.get("objects", {})

            self.timeline_widget.clear_keyframes()
            for kf_index in self.scene_model.keyframes:
                self.timeline_widget.add_keyframe_marker(kf_index)
            
            self._update_timeline_ui_from_model()
            self.scene.setSceneRect(0, 0, self.scene_model.scene_width, self.scene_model.scene_height)
            self._update_background()
            self.go_to_frame(self.scene_model.start_frame)
            self.inspector_widget.refresh()

        except Exception as e:
            print(f"Failed to load scene '{file_path}': {e}")
            self._create_blank_scene()

    def scale_puppet(self, puppet_name, ratio):
        puppet = self.scene_model.puppets.get(puppet_name)
        if not puppet: return
        for member_name in puppet.members:
            piece = self.graphics_items.get(f"{puppet_name}:{member_name}")
            if not piece: continue
            piece.setScale(piece.scale() * ratio)
            if piece.parent_piece: piece.rel_to_parent = (piece.rel_to_parent[0] * ratio, piece.rel_to_parent[1] * ratio)
        for root_member in puppet.get_root_members():
            if (root_piece := self.graphics_items.get(f"{puppet_name}:{root_member.name}")):
                for child in root_piece.children: child.update_transform_from_parent()

    def delete_puppet(self, puppet_name):
        if (puppet := self.scene_model.puppets.get(puppet_name)):
            for member_name in list(puppet.members.keys()):
                if (piece := self.graphics_items.pop(f"{puppet_name}:{member_name}", None)):
                    self.scene.removeItem(piece)
                    if piece.pivot_handle: self.scene.removeItem(piece.pivot_handle)
                    if piece.rotation_handle: self.scene.removeItem(piece.rotation_handle)
            self.scene_model.remove_puppet(puppet_name)
            self.puppet_scales.pop(puppet_name, None)
            self.puppet_paths.pop(puppet_name, None)

    def duplicate_puppet(self, puppet_name):
        if not (path := self.puppet_paths.get(puppet_name)): return
        base = puppet_name; i = 1
        while (new_name := f"{base}_{i}") in self.scene_model.puppets: i += 1
        self.add_puppet(path, new_name)
        if (scale := self.puppet_scales.get(puppet_name, 1.0)) != 1.0:
            self.puppet_scales[new_name] = scale
            self.scale_puppet(new_name, scale)

    def delete_object(self, name):
        if (item := self.graphics_items.pop(name, None)): self.scene.removeItem(item)
        self.scene_model.remove_object(name)

    def duplicate_object(self, name):
        if not (obj := self.scene_model.objects.get(name)): return
        base = name; i = 1
        while (new_name := f"{base}_{i}") in self.scene_model.objects: i += 1
        new_obj = SceneObject(new_name, obj.obj_type, obj.file_path, x=obj.x + 10, y=obj.y + 10, rotation=obj.rotation, scale=obj.scale)
        self.scene_model.add_object(new_obj)
        self._add_object_graphics(new_obj)

    def _add_object_graphics(self, obj: SceneObject):
        item = QGraphicsPixmapItem(obj.file_path) if obj.obj_type == "image" else QGraphicsSvgItem(obj.file_path)
        item.setPos(obj.x, obj.y); item.setRotation(obj.rotation); item.setScale(obj.scale)
        item.setFlag(QGraphicsItem.ItemIsMovable, True); item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.scene.addItem(item)
        self.graphics_items[obj.name] = item
