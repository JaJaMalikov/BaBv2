import logging
import math
from pathlib import Path
from typing import Optional, Any, Dict, List, Tuple

from PySide6.QtWidgets import (
    QMainWindow,
    QGraphicsScene,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QGraphicsPixmapItem,
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QFrame,
    QListWidget, # Added
    QListWidgetItem, # Added
    QGraphicsItem,
    QToolButton,
)
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtGui import QPainter, QPixmap, QAction, QColor, QPen
from PySide6.QtCore import Qt, QTimer, QEvent, QRectF, QPointF

from core.scene_model import SceneModel, SceneObject, Keyframe
from core.puppet_piece import PuppetPiece
from ui.timeline_widget import TimelineWidget
from ui.inspector_widget import InspectorWidget
from ui.library_widget import LibraryWidget
from ui.zoomable_view import ZoomableView
from ui.playback_handler import PlaybackHandler
from ui.object_manager import ObjectManager
from ui.draggable_widget import PanelOverlay, DraggableHeader
from ui.styles import BUTTON_STYLE
import ui.scene_io as scene_io
from ui.icons import (
    icon_scene_size, icon_background, icon_library, icon_inspector, icon_timeline,
    icon_save, icon_open, icon_close,
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Borne and the Bayrou - Disco MIX")

        self.scene_model: SceneModel = SceneModel()
        self.background_item: Optional[QGraphicsPixmapItem] = None
        self.zoom_factor: float = 1.0
        self._suspend_item_updates: bool = False

        self.scene: QGraphicsScene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.scene_model.scene_width, self.scene_model.scene_height)

        self.object_manager: ObjectManager = ObjectManager(self)

        self.view: ZoomableView = ZoomableView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setBackgroundBrush(QColor("#121212"))
        self.view.setFrameShape(QFrame.NoFrame)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Build large overlays (library, inspector) before actions so toggles can bind
        self._build_side_overlays()

        # Onion skin settings
        self.onion_enabled: bool = False
        self.onion_prev_count: int = 2
        self.onion_next_count: int = 1
        self.onion_opacity_prev: float = 0.25
        self.onion_opacity_next: float = 0.18
        self._onion_items: List[QGraphicsItem] = []

        main_widget: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view)
        self.setCentralWidget(main_widget)

        self.timeline_dock: QDockWidget = QDockWidget("", self)
        self.timeline_dock.setObjectName("dock_timeline")
        self.timeline_widget: TimelineWidget = TimelineWidget()
        self.timeline_dock.setWidget(self.timeline_widget)
        self.timeline_dock.setFeatures(QDockWidget.DockWidgetClosable)
        try:
            from PySide6.QtWidgets import QWidget as _QW
            self.timeline_dock.setTitleBarWidget(_QW())
        except Exception:
            pass
        self.addDockWidget(Qt.BottomDockWidgetArea, self.timeline_dock)

        # Inspector and Library now live as overlays (see _build_side_overlays)

        self.playback_handler: PlaybackHandler = PlaybackHandler(self.scene_model, self.timeline_widget, self.inspector_widget, self)

        self._create_actions()
        self.view._build_main_tools_overlay(self)
        self.connect_signals()
        self._setup_scene_visuals()
        self._apply_unified_stylesheet()

        # --- Startup Sequence ---
        self.showMaximized()
        # Overlays start hidden for a clean canvas
        self.inspector_overlay.hide()
        self.library_overlay.hide()
        self.timeline_dock.show()
        self.timeline_dock.visibilityChanged.connect(lambda _: self.ensure_fit())
        self.timeline_dock.topLevelChanged.connect(lambda _: self.ensure_fit())
        self.ensure_fit()
        scene_io.create_blank_scene(self, add_default_puppet=False)
        self.ensure_fit()
        self.scene.selectionChanged.connect(self._on_scene_selection_changed)

    def showEvent(self, event: QEvent) -> None:
        super().showEvent(event)
        def _layout_then_fit():
            try:
                self.resizeDocks([self.timeline_dock], [int(max(140, self.height()*0.22))], Qt.Vertical)
            except Exception:
                pass
            self.fit_to_view()
            self._position_overlays()
        QTimer.singleShot(0, _layout_then_fit)
        QTimer.singleShot(200, self._position_overlays)

    def _position_overlays(self) -> None:
        # Open both panels positioned like former docks
        if not self.library_overlay.isVisible():
            self.library_overlay.show()
        if not self.inspector_overlay.isVisible():
            self.inspector_overlay.show()
        try:
            self.toggle_library_action.blockSignals(True)
            self.toggle_inspector_action.blockSignals(True)
            self.toggle_library_action.setChecked(True)
            self.toggle_inspector_action.setChecked(True)
        finally:
            self.toggle_library_action.blockSignals(False)
            self.toggle_inspector_action.blockSignals(False)
        margin = 10
        # Library on the left
        lib_w = self.library_overlay.width(); lib_h = min(self.height() - 2*margin - 120, self.library_overlay.height())
        self.library_overlay.resize(lib_w, lib_h)
        self.library_overlay.move(margin, margin)
        # Inspector on the right
        insp_w = self.inspector_overlay.width(); insp_h = min(self.height() - 2*margin - 120, self.inspector_overlay.height())
        self.inspector_overlay.resize(insp_w, insp_h)
        self.inspector_overlay.move(self.width() - insp_w - margin, margin)
        # Menu overlays: place top area between the two panels
        try:
            left_bound = self.library_overlay.x() + self.library_overlay.width() + margin
            right_bound = self.inspector_overlay.x() - margin
            # Access overlays from view
            ov = getattr(self.view, "_overlay", None)
            mov = getattr(self.view, "_main_tools_overlay", None)
            if ov:
                ov.adjustSize(); ov.move(left_bound, margin)
            if mov:
                mov.adjustSize(); mov.move(max(left_bound, right_bound - mov.width()), margin)
        except Exception:
            pass

    def _create_actions(self) -> None:
        self.save_action: QAction = QAction(icon_save(), "Sauvegarder (Ctrl+S)", self)
        self.save_action.setShortcut("Ctrl+S")
        self.load_action: QAction = QAction(icon_open(), "Charger (Ctrl+O)", self)
        self.load_action.setShortcut("Ctrl+O")
        self.scene_size_action: QAction = QAction(icon_scene_size(), "Taille Scène", self)
        self.background_action: QAction = QAction(icon_background(), "Image de fond", self)

        # Overlay toggles
        self.toggle_library_action: QAction = QAction(icon_library(), "Bibliothèque", self)
        self.toggle_library_action.setCheckable(True)
        self.toggle_library_action.setChecked(self.library_overlay.isVisible())
        self.toggle_library_action.toggled.connect(self.set_library_overlay_visible)

        self.toggle_inspector_action: QAction = QAction(icon_inspector(), "Inspecteur", self)
        self.toggle_inspector_action.setCheckable(True)
        self.toggle_inspector_action.setChecked(self.inspector_overlay.isVisible())
        self.toggle_inspector_action.toggled.connect(self.set_inspector_overlay_visible)

        # Timeline toggle (dock)
        self.timeline_dock.toggleViewAction().setIcon(icon_timeline())

    def connect_signals(self) -> None:
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
        self.view.onion_toggled.connect(self.set_onion_enabled)
        self.view.item_dropped.connect(self.object_manager.handle_library_drop)

        # PlaybackHandler signals
        self.playback_handler.snapshot_requested.connect(self.object_manager.snapshot_current_frame)
        self.playback_handler.frame_update_requested.connect(self._on_frame_update)
        self.playback_handler.keyframe_add_requested.connect(self.add_keyframe)

        # Library signals
        self.library_widget.addRequested.connect(self.object_manager._add_library_item_to_scene)


    def _apply_unified_stylesheet(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #101112; }
            QDockWidget { titlebar-close-icon: none; titlebar-normal-icon: none; background: #131011; color: #E6E6E6; border: 1px solid #2C1718; }
            QDockWidget::title { background: #160C0D; padding: 6px 10px; border-bottom: 1px solid #3C1B1C; color: #F6E9E9; }
            QListWidget, QTreeWidget { background: #121012; color: #E6E6E6; border: 1px solid #2C1718; }
            QListWidget::item:selected, QTreeWidget::item:selected { background: rgba(229,57,53,0.35); color: #FFFFFF; }
            QListWidget::item:hover, QTreeWidget::item:hover { background: rgba(229,57,53,0.15); }
            QTreeWidget { alternate-background-color: rgba(255,255,255,0.03); }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: #120E0F; color: #E6E6E6; border: 1px solid #3C1B1C; selection-background-color: rgba(229,57,53,0.55); border-radius: 6px; padding: 2px 4px; }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: rgba(229,57,53,0.7); }
            QLabel { color: #F2DDDD; }
            QLabel[role="section-title"] { color: #F28C8C; font-weight: 600; }
            QWidget[role="card"] { background: #151113; border: 1px solid #3C1B1C; border-radius: 12px; }
            QWidget[role="overlay-header"] { background: rgba(0,0,0,0.15); border-bottom: 1px solid rgba(229,57,53,0.25); border-top-left-radius: 12px; border-top-right-radius: 12px; }
            QLabel[role="overlay-header-title"] { color: #F6E9E9; font-weight: 600; }
            QToolTip { color: #FFFFFF; background-color: rgba(229,57,53,0.85); border: 1px solid #B71C1C; }
            """
        )

    def _build_side_overlays(self) -> None:
        # Library overlay
        self.library_overlay = PanelOverlay(self.view)
        self.library_overlay.setVisible(False)
        lib_layout = QVBoxLayout(self.library_overlay)
        lib_layout.setContentsMargins(8, 8, 8, 8)
        lib_layout.setSpacing(6)
        # Header (HUD)
        lib_header = DraggableHeader(self.library_overlay, parent=self.library_overlay)
        h1 = QHBoxLayout(lib_header); h1.setContentsMargins(8, 6, 8, 6); h1.setSpacing(6)
        lbl_lib = QLabel("Bibliothèque", lib_header)
        lbl_lib.setProperty("role", "overlay-header-title")
        btn_close_lib = QToolButton(lib_header); btn_close_lib.setIcon(icon_close()); btn_close_lib.setStyleSheet(BUTTON_STYLE); btn_close_lib.setAutoRaise(True)
        btn_close_lib.clicked.connect(lambda: self.set_library_overlay_visible(False))
        h1.addWidget(lbl_lib); h1.addStretch(1); h1.addWidget(btn_close_lib)
        lib_layout.addWidget(lib_header)
        self.library_widget = LibraryWidget(root_dir=str(Path.cwd()), parent=self.library_overlay)
        lib_layout.addWidget(self.library_widget)
        self.library_overlay.resize(360, 520)
        self.library_overlay.move(10, 100)

        # Inspector overlay (hidden by default)
        self.inspector_overlay = PanelOverlay(self.view)
        self.inspector_overlay.setVisible(False)
        insp_layout = QVBoxLayout(self.inspector_overlay)
        insp_layout.setContentsMargins(8, 8, 8, 8)
        insp_layout.setSpacing(6)
        # Header (HUD)
        insp_header = DraggableHeader(self.inspector_overlay, parent=self.inspector_overlay)
        h2 = QHBoxLayout(insp_header); h2.setContentsMargins(8, 6, 8, 6); h2.setSpacing(6)
        lbl_insp = QLabel("Inspecteur", insp_header)
        lbl_insp.setProperty("role", "overlay-header-title")
        btn_close_insp = QToolButton(insp_header); btn_close_insp.setIcon(icon_close()); btn_close_insp.setStyleSheet(BUTTON_STYLE); btn_close_insp.setAutoRaise(True)
        btn_close_insp.clicked.connect(lambda: self.set_inspector_overlay_visible(False))
        h2.addWidget(lbl_insp); h2.addStretch(1); h2.addWidget(btn_close_insp)
        insp_layout.addWidget(insp_header)
        self.inspector_widget = InspectorWidget(self)
        insp_layout.addWidget(self.inspector_widget)
        self.inspector_overlay.resize(380, 560)
        self.inspector_overlay.move(400, 100)

    def set_library_overlay_visible(self, visible: bool) -> None:
        self.library_overlay.setVisible(visible)
        self.toggle_library_action.blockSignals(True)
        self.toggle_library_action.setChecked(visible)
        self.toggle_library_action.blockSignals(False)

    def set_inspector_overlay_visible(self, visible: bool) -> None:
        self.inspector_overlay.setVisible(visible)
        self.toggle_inspector_action.blockSignals(True)
        self.toggle_inspector_action.setChecked(visible)
        self.toggle_inspector_action.blockSignals(False)

    def _setup_scene_visuals(self) -> None:
        self.scene_border_item: QGraphicsRectItem = QGraphicsRectItem(); self.scene_size_text_item: QGraphicsTextItem = QGraphicsTextItem()
        self.scene.addItem(self.scene_border_item); self.scene.addItem(self.scene_size_text_item)
        self._update_scene_visuals()

    def _update_scene_visuals(self) -> None:
        rect: QRectF = self.scene.sceneRect()
        self.scene_border_item.setPen(QPen(QColor(100, 100, 100), 2, Qt.DashLine)); self.scene_border_item.setRect(rect)
        text: str = f"{self.scene_model.scene_width}x{self.scene_model.scene_height}"
        self.scene_size_text_item.setPlainText(text); self.scene_size_text_item.setDefaultTextColor(QColor(150, 150, 150))
        text_rect: QRectF = self.scene_size_text_item.boundingRect()
        self.scene_size_text_item.setPos(rect.right() - text_rect.width() - 10, rect.bottom() - text_rect.height() - 10)

    def _update_zoom_status(self) -> None:
        # No status bar or zoom label; keep overlay minimal
        pass

    def zoom(self, factor: float) -> None:
        self.view.scale(factor, factor)
        self.zoom_factor *= factor
        self._update_zoom_status()

    def fit_to_view(self) -> None:
        self.view.resetTransform()
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.zoom_factor = self.view.transform().m11()
        self._update_zoom_status()

    def ensure_fit(self) -> None:
        QTimer.singleShot(0, self.fit_to_view)

    def set_scene_size(self) -> None:
        width: int
        ok1: bool
        width, ok1 = QInputDialog.getInt(self, "Taille de la scène", "Largeur:", self.scene_model.scene_width, 1)
        if ok1:
            height: int
            ok2: bool
            height, ok2 = QInputDialog.getInt(self, "Taille de la scène", "Hauteur:", self.scene_model.scene_height, 1)
            if ok2:
                self.scene_model.scene_width = width
                self.scene_model.scene_height = height
                self.scene.setSceneRect(0, 0, width, height)
                self._update_scene_visuals()
                self._update_background()
                self._update_zoom_status()

    def set_background(self) -> None:
        filePath: str
        filePath, _ = QFileDialog.getOpenFileName(self, "Charger une image d'arrière-plan", "", "Images (*.png *.jpg *.jpeg)")
        if filePath:
            self.scene_model.background_path = filePath
            self._update_background()

    def _update_background(self):
        if self.background_item:
            self.scene.removeItem(self.background_item)
            self.background_item = None
        if self.scene_model.background_path:
            try:
                pixmap = QPixmap(self.scene_model.background_path)
                if pixmap.isNull():
                    raise FileNotFoundError(f"Could not load image: {self.scene_model.background_path}")
                self.scene_model.scene_width = pixmap.width()
                self.scene_model.scene_height = pixmap.height()
                self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
                self._update_scene_visuals()
                self.background_item = QGraphicsPixmapItem(pixmap)
                self.background_item.setZValue(-10000)
                self.scene.addItem(self.background_item)
                self.ensure_fit()
            except FileNotFoundError as e:
                logging.error(f"Failed to load background image: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred while updating background: {e}")

    def toggle_rotation_handles(self, visible: bool) -> None:
        for item in self.object_manager.graphics_items.values():
            if isinstance(item, PuppetPiece):
                item.set_handle_visibility(visible)
        self.view.handles_btn.setChecked(visible)

    def update_scene_from_model(self) -> None:
        index: int = self.scene_model.current_frame
        keyframes: Dict[int, Keyframe] = self.scene_model.keyframes
        if not keyframes:
            return

        graphics_items: Dict[str, Any] = self.object_manager.graphics_items
        logging.debug(f"update_scene_from_model: frame={index}, keyframes={list(keyframes.keys())}")

        self._apply_puppet_states(graphics_items, keyframes, index)
        self._apply_object_states(graphics_items, keyframes, index)

    def _apply_puppet_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Keyframe], index: int) -> None:
        sorted_indices: List[int] = sorted(keyframes.keys())
        prev_kf_index: int = next((i for i in reversed(sorted_indices) if i <= index), -1)
        next_kf_index: int = next((i for i in sorted(sorted_indices) if i > index), -1)

        if prev_kf_index != -1 and next_kf_index != -1 and prev_kf_index != next_kf_index:
            prev_kf: Keyframe = keyframes[prev_kf_index]
            next_kf: Keyframe = keyframes[next_kf_index]
            ratio: float = (index - prev_kf_index) / (next_kf_index - prev_kf_index)
            for name, puppet in self.scene_model.puppets.items():
                prev_pose: Dict[str, Dict[str, Any]] = prev_kf.puppets.get(name, {})
                next_pose: Dict[str, Dict[str, Any]] = next_kf.puppets.get(name, {})
                for member_name in puppet.members:
                    prev_state: Optional[Dict[str, Any]] = prev_pose.get(member_name)
                    next_state: Optional[Dict[str, Any]] = next_pose.get(member_name)
                    if not prev_state or not next_state:
                        continue
                    interp_rot: float = prev_state['rotation'] + (next_state['rotation'] - prev_state['rotation']) * ratio
                    piece: PuppetPiece = graphics_items[f"{name}:{member_name}"]
                    piece.local_rotation = interp_rot
                    if not piece.parent_piece:
                        prev_pos: Tuple[float, float] = prev_state['pos']
                        next_pos: Tuple[float, float] = next_state['pos']
                        interp_x: float = prev_pos[0] + (next_pos[0] - prev_pos[0]) * ratio
                        interp_y: float = prev_pos[1] + (next_pos[1] - prev_pos[1]) * ratio
                        piece.setPos(interp_x, interp_y)
        else:
            target_kf_index: int = prev_kf_index if prev_kf_index != -1 else next_kf_index
            if target_kf_index == -1:
                return
            kf: Keyframe = keyframes[target_kf_index]
            for name, state in kf.puppets.items():
                for member, member_state in state.items():
                    piece: PuppetPiece = graphics_items[f"{name}:{member}"]
                    piece.local_rotation = member_state['rotation']
                    if not piece.parent_piece:
                        piece.setPos(*member_state['pos'])

        # Propager transformations aux enfants
        for name, puppet in self.scene_model.puppets.items():
            for root_member in puppet.get_root_members():
                root_piece: PuppetPiece = graphics_items[f"{name}:{root_member.name}"]
                root_piece.setRotation(root_piece.local_rotation)
                for child in root_piece.children:
                    child.update_transform_from_parent()

    def _apply_object_states(self, graphics_items: Dict[str, Any], keyframes: Dict[int, Keyframe], index: int) -> None:
        def state_for(obj_name: str) -> Optional[Dict[str, Any]]:
            si: List[int] = sorted(keyframes.keys())
            last_kf: Optional[int] = next((i for i in reversed(si) if i <= index), None)
            if last_kf is not None and obj_name not in keyframes[last_kf].objects:
                return None
            prev_including: Optional[int] = next((i for i in reversed(si) if i <= index and obj_name in keyframes[i].objects), None)
            if prev_including is None:
                return None
            return keyframes[prev_including].objects.get(obj_name)

        updated: int = 0
        self._suspend_item_updates = True
        try:
            for name, base_obj in self.scene_model.objects.items():
                st: Optional[Dict[str, Any]] = state_for(name)
                gi: Optional[QGraphicsItem] = graphics_items.get(name)
                if st is None:
                    if gi:
                        gi.setSelected(False)
                        gi.setVisible(False)
                    continue
                if gi is None:
                    tmp: SceneObject = SceneObject(
                        name,
                        st.get('obj_type', base_obj.obj_type),
                        st.get('file_path', base_obj.file_path),
                        x=st.get('x', base_obj.x),
                        y=st.get('y', base_obj.y),
                        rotation=st.get('rotation', base_obj.rotation),
                        scale=st.get('scale', base_obj.scale),
                        z=st.get('z', getattr(base_obj, 'z', 0))
                    )
                    self.object_manager._add_object_graphics(tmp)
                    gi = graphics_items.get(name)
                if gi:
                    gi.setVisible(True)
                    attached: Optional[Tuple[str, str]] = st.get('attached_to', None)
                    if attached:
                        puppet_name, member_name = attached
                        parent_piece: Optional[PuppetPiece] = graphics_items.get(f"{puppet_name}:{member_name}")
                        # Always set the parent first, then apply the saved local transform
                        if parent_piece is not None and gi.parentItem() is not parent_piece:
                            gi.setParentItem(parent_piece)
                        # Apply local coordinates from state (default to 0,0)
                        gi.setPos(float(st.get('x', 0.0)), float(st.get('y', 0.0)))
                    else:
                        # Ensure the item is in scene coordinates
                        if gi.parentItem() is not None:
                            gi.setParentItem(None)
                        gi.setPos(float(st.get('x', gi.x())), float(st.get('y', gi.y())))
                    gi.setRotation(float(st.get('rotation', gi.rotation())))
                    gi.setScale(float(st.get('scale', gi.scale())))
                    gi.setZValue(int(st.get('z', int(gi.zValue()))))
                    updated += 1
        finally:
            self._suspend_item_updates = False
        logging.debug(f"Applied object states: {updated} updated/visible")

    def add_keyframe(self, frame_index: int) -> None:
        puppet_states: Dict[str, Dict[str, Dict[str, Any]]] = self.object_manager.capture_puppet_states()
        self.scene_model.add_keyframe(frame_index, puppet_states)
        # Overwrite objects with the on-screen capture so we don't serialize stale/global attachment
        kf: Optional[Keyframe] = self.scene_model.keyframes.get(frame_index)
        if kf is not None:
            kf.objects = self.object_manager.capture_visible_object_states()
        self.timeline_widget.add_keyframe_marker(frame_index)

    def select_object_in_inspector(self, name: str) -> None:
        if not hasattr(self, 'inspector_widget') or not self.inspector_widget:
            return
        lw: QListWidget = self.inspector_widget.list_widget
        for i in range(lw.count()):
            it: QListWidgetItem = lw.item(i)
            typ: str
            nm: str
            typ, nm = it.data(Qt.UserRole)
            if typ == 'object' and nm == name:
                lw.setCurrentItem(it)
                break

    def _on_scene_selection_changed(self) -> None:
        for item in self.scene.selectedItems():
            for name, gi in self.object_manager.graphics_items.items():
                if gi is item and name in self.scene_model.objects:
                    self.select_object_in_inspector(name)
                    return
    def _on_frame_update(self) -> None:
        self.update_scene_from_model()
        self.update_onion_skins()

    def set_onion_enabled(self, enabled: bool) -> None:
        self.onion_enabled = enabled
        self.update_onion_skins()

    def clear_onion_skins(self) -> None:
        # Remove only root onion items to avoid Qt warnings when children lose their scene
        for it in list(self._onion_items):
            try:
                if it and it.parentItem() is None and it.scene() is self.scene:
                    self.scene.removeItem(it)
            except Exception:
                pass
        self._onion_items.clear()

    def update_onion_skins(self) -> None:
        self.clear_onion_skins()
        if not self.onion_enabled:
            return
        cur: int = self.scene_model.current_frame
        # Previous frames
        for k in range(1, self.onion_prev_count + 1):
            idx = max(self.scene_model.start_frame, cur - k)
            if idx == cur:
                continue
            self._add_onion_for_frame(idx, self.onion_opacity_prev, z_offset=-200)
        # Next frames
        for k in range(1, self.onion_next_count + 1):
            idx = min(self.scene_model.end_frame, cur + k)
            if idx == cur:
                continue
            self._add_onion_for_frame(idx, self.onion_opacity_next, z_offset=-300)

    def _add_onion_for_frame(self, frame_index: int, opacity: float, z_offset: int = -200) -> None:
        # Puppets only (first iteration): draw ghost poses based on last keyframe <= index
        keyframes = self.scene_model.keyframes
        if not keyframes:
            return
        sorted_indices: List[int] = sorted(keyframes.keys())
        target_kf_index: Optional[int] = next((i for i in reversed(sorted_indices) if i <= frame_index), None)
        if target_kf_index is None:
            return
        kf: Keyframe = keyframes[target_kf_index]
        graphics_items: Dict[str, Any] = self.object_manager.graphics_items

        # Clone puppets
        clones_map: Dict[str, PuppetPiece] = {}
        for puppet_name, puppet in self.scene_model.puppets.items():
            puppet_state: Dict[str, Dict[str, Any]] = kf.puppets.get(puppet_name, {})
            if not puppet_state:
                continue
            # Create clones for each member
            clones: Dict[str, PuppetPiece] = {}
            for member_name in puppet.members:
                base_piece: PuppetPiece = graphics_items.get(f"{puppet_name}:{member_name}")
                if not base_piece:
                    continue
                # Create lightweight clone sharing the renderer
                clone: PuppetPiece = PuppetPiece("", member_name, base_piece.transformOriginPoint().x(), base_piece.transformOriginPoint().y(), renderer=self.object_manager.renderers.get(puppet_name))
                clone.setOpacity(opacity)
                clone.setZValue(base_piece.zValue() + z_offset)
                clone.setFlag(QGraphicsItem.ItemIsSelectable, False)
                clone.setFlag(QGraphicsItem.ItemIsMovable, False)
                self.scene.addItem(clone)
                self._onion_items.append(clone)
                clones[member_name] = clone
                clones_map[f"{puppet_name}:{member_name}"] = clone

            # Position roots then propagate to children using base rel_to_parent
            for root_member in puppet.get_root_members():
                root_name = root_member.name
                clone_root: Optional[PuppetPiece] = clones.get(root_name)
                state = puppet_state.get(root_name)
                if clone_root is None or state is None:
                    continue
                clone_root.setPos(*state.get('pos', (clone_root.x(), clone_root.y())))
                clone_root.setRotation(state.get('rotation', 0.0))

            # Recursive propagation
            def propagate(member_name: str) -> None:
                base_piece: PuppetPiece = graphics_items.get(f"{puppet_name}:{member_name}")
                clone_piece: PuppetPiece = clones.get(member_name)
                if not base_piece or not clone_piece:
                    return
                for child in base_piece.children:
                    child_clone: Optional[PuppetPiece] = clones.get(child.name)
                    if child_clone is None:
                        continue
                    # Parent global rotation
                    parent_rot: float = clone_piece.rotation()
                    angle_rad: float = parent_rot * math.pi / 180.0
                    dx, dy = child.rel_to_parent
                    cos_a = math.cos(angle_rad)
                    sin_a = math.sin(angle_rad)
                    rotated_dx: float = dx * cos_a - dy * sin_a
                    rotated_dy: float = dx * sin_a + dy * cos_a
                    parent_pivot_scene: QPointF = clone_piece.mapToScene(clone_piece.transformOriginPoint())
                    scene_x: float = parent_pivot_scene.x() + rotated_dx
                    scene_y: float = parent_pivot_scene.y() + rotated_dy
                    child_clone.setPos(scene_x - child_clone.transformOriginPoint().x(), scene_y - child_clone.transformOriginPoint().y())
                    child_state = puppet_state.get(child.name, {})
                    child_clone.setRotation(parent_rot + child_state.get('rotation', 0.0))
                    propagate(child.name)

            for root_member in puppet.get_root_members():
                propagate(root_member.name)

        # Clone objects state for this frame and attach to puppet clones if needed
        def object_state_for(obj_name: str) -> Optional[Dict[str, Any]]:
            si: List[int] = sorted(keyframes.keys())
            last_kf: Optional[int] = next((i for i in reversed(si) if i <= frame_index), None)
            if last_kf is not None and obj_name not in keyframes[last_kf].objects:
                return None
            prev_including: Optional[int] = next((i for i in reversed(si) if i <= frame_index and obj_name in keyframes[i].objects), None)
            if prev_including is None:
                return None
            return keyframes[prev_including].objects.get(obj_name)

        for name, base_obj in self.scene_model.objects.items():
            st: Optional[Dict[str, Any]] = object_state_for(name)
            if not st:
                continue
            try:
                if st.get('obj_type') == 'image':
                    pm = QPixmap(st.get('file_path', base_obj.file_path))
                    item: QGraphicsItem = QGraphicsPixmapItem(pm)
                else:
                    item = QGraphicsSvgItem(st.get('file_path', base_obj.file_path))
                # Avoid model feedback
                item.setFlag(QGraphicsItem.ItemIsMovable, False)
                item.setFlag(QGraphicsItem.ItemIsSelectable, False)
                item.setOpacity(opacity)
                # Transform origin for proper rotation
                if hasattr(item, 'boundingRect') and not item.boundingRect().isEmpty():
                    item.setTransformOriginPoint(item.boundingRect().center())
                # Attachment to puppet clone if required
                attached = st.get('attached_to')
                if attached:
                    try:
                        puppet_name, member_name = attached
                        parent_clone: Optional[PuppetPiece] = clones_map.get(f"{puppet_name}:{member_name}")
                        if parent_clone is not None:
                            item.setParentItem(parent_clone)
                            # Local transform (relative to parent clone)
                            item.setScale(st.get('scale', getattr(base_obj, 'scale', 1.0)))
                            item.setRotation(st.get('rotation', getattr(base_obj, 'rotation', 0.0)))
                            item.setZValue(st.get('z', getattr(base_obj, 'z', 0)) + z_offset)
                            item.setPos(st.get('x', getattr(base_obj, 'x', 0.0)), st.get('y', getattr(base_obj, 'y', 0.0)))
                            # Parent clone is already in scene; no need to add child explicitly
                        else:
                            # Fallback: place as free object in world
                            item.setScale(st.get('scale', getattr(base_obj, 'scale', 1.0)))
                            item.setRotation(st.get('rotation', getattr(base_obj, 'rotation', 0.0)))
                            item.setZValue(st.get('z', getattr(base_obj, 'z', 0)) + z_offset)
                            item.setPos(st.get('x', getattr(base_obj, 'x', 0.0)), st.get('y', getattr(base_obj, 'y', 0.0)))
                            self.scene.addItem(item)
                            self._onion_items.append(item)
                    except Exception as e:
                        logging.error(f"Onion attach failed for object {name}: {e}")
                else:
                    # Free object in world coordinates
                    item.setScale(st.get('scale', getattr(base_obj, 'scale', 1.0)))
                    item.setRotation(st.get('rotation', getattr(base_obj, 'rotation', 0.0)))
                    item.setZValue(st.get('z', getattr(base_obj, 'z', 0)) + z_offset)
                    item.setPos(st.get('x', getattr(base_obj, 'x', 0.0)), st.get('y', getattr(base_obj, 'y', 0.0)))
                    self.scene.addItem(item)
                    self._onion_items.append(item)
            except Exception as e:
                logging.error(f"Onion object clone failed for {name}: {e}")
