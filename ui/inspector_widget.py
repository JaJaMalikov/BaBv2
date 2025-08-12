from PySide6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QComboBox, QToolButton, QFormLayout, QFrame
)
from PySide6.QtCore import Qt
from ui.icons import icon_delete, icon_duplicate, icon_link, icon_link_off

class InspectorWidget(QWidget):
    """Simple inspector to manage scene objects and puppets."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # --- WIDGET CREATION ---
        self.list_widget = QListWidget()

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 10.0)
        self.scale_spin.setSingleStep(0.1)
        self.rot_spin = QDoubleSpinBox()
        self.rot_spin.setRange(-360.0, 360.0)
        self.rot_spin.setSingleStep(1.0)
        self.z_spin = QDoubleSpinBox()
        self.z_spin.setRange(-10000, 10000)
        self.z_spin.setSingleStep(1)

        self.attach_puppet_combo = QComboBox()
        self.attach_member_combo = QComboBox()
        self.attach_btn = QToolButton()
        self.attach_btn.setIcon(icon_link())
        self.attach_btn.setToolTip("Lier l'objet au membre")
        self.detach_btn = QToolButton()
        self.detach_btn.setIcon(icon_link_off())
        self.detach_btn.setToolTip("Détacher l'objet")

        self.duplicate_btn = QToolButton()
        self.duplicate_btn.setIcon(icon_duplicate())
        self.duplicate_btn.setToolTip("Dupliquer")
        self.delete_btn = QToolButton()
        self.delete_btn.setIcon(icon_delete())
        self.delete_btn.setToolTip("Supprimer")

        # --- LAYOUT ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        main_layout.addWidget(self.list_widget)

        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setLabelAlignment(Qt.AlignRight)

        form_layout.addRow("Échelle:", self.scale_spin)
        form_layout.addRow("Rotation:", self.rot_spin)
        form_layout.addRow("Z-Order:", self.z_spin)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        form_layout.addRow(line)

        form_layout.addRow("Attacher à:", self.attach_puppet_combo)
        form_layout.addRow("Membre:", self.attach_member_combo)

        attach_actions_layout = QHBoxLayout()
        attach_actions_layout.addStretch()
        attach_actions_layout.addWidget(self.attach_btn)
        attach_actions_layout.addWidget(self.detach_btn)
        form_layout.addRow("", attach_actions_layout)

        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        form_layout.addRow(line2)

        main_actions_layout = QHBoxLayout()
        main_actions_layout.addStretch()
        main_actions_layout.addWidget(self.duplicate_btn)
        main_actions_layout.addWidget(self.delete_btn)
        form_layout.addRow("Actions:", main_actions_layout)

        main_layout.addLayout(form_layout)

        # --- CONNECTIONS ---
        self.list_widget.currentItemChanged.connect(self._on_item_changed)
        self.scale_spin.valueChanged.connect(self._on_scale_changed)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.duplicate_btn.clicked.connect(self._on_duplicate_clicked)
        self.rot_spin.valueChanged.connect(self._on_rotation_changed)
        self.z_spin.valueChanged.connect(self._on_z_changed)
        self.attach_puppet_combo.currentTextChanged.connect(self._on_attach_puppet_changed)
        self.attach_btn.clicked.connect(self._on_attach_clicked)
        self.detach_btn.clicked.connect(self._on_detach_clicked)

        self.refresh()

    def refresh(self):
        """Refresh list from scene model."""
        self.list_widget.clear()
        model = self.main_window.scene_model
        for name in sorted(model.puppets.keys()):
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, ("puppet", name))
            self.list_widget.addItem(item)
        for name in sorted(model.objects.keys()):
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, ("object", name))
            self.list_widget.addItem(item)
        self._refresh_attach_puppet_combo()

    # --- Callbacks ---
    def _current_info(self):
        item = self.list_widget.currentItem()
        if not item:
            return None, None
        return item.data(Qt.UserRole)

    def _on_item_changed(self, current, previous):
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            obj = self.main_window.scene_model.objects.get(name)
            scale = obj.scale if obj else 1.0
            rot = obj.rotation if obj else 0.0
            z = getattr(obj, 'z', 0)
            # Sélectionner l'objet dans la scène
            for it in self.main_window.scene.selectedItems():
                it.setSelected(False)
            gi = self.main_window.object_manager.graphics_items.get(name)
            if gi and gi.isVisible():
                gi.setSelected(True)
            # Pré-sélectionner les combos selon l'état à la frame courante
            pu, me = self._attached_state_for_frame(name)
            self._refresh_attach_puppet_combo()
            if pu:
                idx = self.attach_puppet_combo.findText(pu)
                if idx >= 0:
                    self.attach_puppet_combo.setCurrentIndex(idx)
                    self._refresh_attach_member_combo()
                    midx = self.attach_member_combo.findText(me) if me else -1
                    if midx >= 0:
                        self.attach_member_combo.setCurrentIndex(midx)
            else:
                self.attach_puppet_combo.setCurrentIndex(0)
                self._refresh_attach_member_combo()
        else:
            scale = self.main_window.object_manager.puppet_scales.get(name, 1.0)
            rot = 0.0
            z = 0
            # Rien à afficher pour les pantins
        self.scale_spin.blockSignals(True)
        self.scale_spin.setValue(scale)
        self.scale_spin.blockSignals(False)
        self.rot_spin.blockSignals(True)
        self.rot_spin.setValue(rot)
        self.rot_spin.blockSignals(False)
        self.z_spin.blockSignals(True)
        self.z_spin.setValue(z)
        self.z_spin.blockSignals(False)

    def _on_scale_changed(self, value):
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            obj = self.main_window.scene_model.objects.get(name)
            if obj:
                obj.scale = value
                item = self.main_window.object_manager.graphics_items.get(name)
                if item:
                    item.setScale(value)
        else:
            old = self.main_window.object_manager.puppet_scales.get(name, 1.0)
            if value <= 0:
                return
            ratio = value / old if old else value
            self.main_window.object_manager.puppet_scales[name] = value
            self.main_window.object_manager.scale_puppet(name, ratio)

    def _on_delete_clicked(self):
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            # Suppression temporelle: à partir de la frame courante
            self.main_window.object_manager.delete_object_from_current_frame(name)
        else:
            self.main_window.object_manager.delete_puppet(name)
        self.refresh()

    def _on_duplicate_clicked(self):
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            self.main_window.object_manager.duplicate_object(name)
        else:
            self.main_window.object_manager.duplicate_puppet(name)
        self.refresh()

    def _on_rotation_changed(self, value: float):
        typ, name = self._current_info()
        if typ != "object" or not name:
            return
        obj = self.main_window.scene_model.objects.get(name)
        item = self.main_window.object_manager.graphics_items.get(name)
        if obj and item:
            obj.rotation = value
            try:
                item.setTransformOriginPoint(item.boundingRect().center())
            except Exception:
                pass
            item.setRotation(value)

    def _on_z_changed(self, value: float):
        typ, name = self._current_info()
        if typ != "object" or not name:
            return
        obj = self.main_window.scene_model.objects.get(name)
        item = self.main_window.object_manager.graphics_items.get(name)
        if obj and item:
            obj.z = int(value)
            item.setZValue(int(value))

    def _refresh_attach_puppet_combo(self):
        self.attach_puppet_combo.blockSignals(True)
        self.attach_puppet_combo.clear()
        self.attach_puppet_combo.addItem("")
        for name in sorted(self.main_window.scene_model.puppets.keys()):
            self.attach_puppet_combo.addItem(name)
        self.attach_puppet_combo.blockSignals(False)
        self._refresh_attach_member_combo()

    def _refresh_attach_member_combo(self):
        puppet = self.attach_puppet_combo.currentText()
        self.attach_member_combo.clear()
        if puppet and puppet in self.main_window.scene_model.puppets:
            members = sorted(self.main_window.scene_model.puppets[puppet].members.keys())
            self.attach_member_combo.addItems(members)

    def _on_attach_puppet_changed(self, _):
        self._refresh_attach_member_combo()

    def _on_attach_clicked(self):
        typ, name = self._current_info()
        if typ != "object" or not name:
            return
        puppet = self.attach_puppet_combo.currentText()
        member = self.attach_member_combo.currentText()
        if puppet and member:
            self.main_window.object_manager.attach_object_to_member(name, puppet, member)
            self._on_item_changed(self.list_widget.currentItem(), None)

    def _on_detach_clicked(self):
        typ, name = self._current_info()
        if typ != "object" or not name:
            return
        self.main_window.object_manager.detach_object(name)
        self._on_item_changed(self.list_widget.currentItem(), None)

    # --- Helpers ---
    def _attached_state_for_frame(self, obj_name: str):
        """Retourne (puppet_name, member_name) attachés à la frame courante, sinon (None, None).
        Respecte la même politique de visibilité que la scène: si le keyframe le plus
        récent ≤ frame ne contient pas l'objet, on considère l'objet masqué/détaché.
        """
        mw = self.main_window
        idx = mw.scene_model.current_frame
        si = sorted(mw.scene_model.keyframes.keys())
        last_kf = next((i for i in reversed(si) if i <= idx), None)
        if last_kf is not None and obj_name not in mw.scene_model.keyframes[last_kf].objects:
            return (None, None)
        prev = next((i for i in reversed(si) if i <= idx and obj_name in mw.scene_model.keyframes[i].objects), None)
        if prev is None:
            obj = mw.scene_model.objects.get(obj_name)
            return obj.attached_to if obj and obj.attached_to else (None, None)
        st = mw.scene_model.keyframes[prev].objects.get(obj_name, {})
        attached = st.get('attached_to')
        if attached:
            try:
                pu, me = attached
                return pu, me
            except Exception:
                return (None, None)
        return (None, None)

    def sync_with_frame(self):
        """À appeler quand la frame courante change pour resynchroniser les combos."""
        cur = self.list_widget.currentItem()
        if cur is not None:
            self._on_item_changed(cur, None)