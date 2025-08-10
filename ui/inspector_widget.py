from PySide6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton, QComboBox
)
from PySide6.QtCore import Qt

class InspectorWidget(QWidget):
    """Simple inspector to manage scene objects and puppets."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

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
        self.duplicate_btn = QPushButton("Dupliquer")
        self.delete_btn = QPushButton("Supprimer")
        self.attach_puppet_combo = QComboBox()
        self.attach_member_combo = QComboBox()
        self.attach_btn = QPushButton("Lier")
        self.detach_btn = QPushButton("Détacher")

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)

        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Échelle"))
        scale_layout.addWidget(self.scale_spin)
        layout.addLayout(scale_layout)

        rot_layout = QHBoxLayout()
        rot_layout.addWidget(QLabel("Rotation"))
        rot_layout.addWidget(self.rot_spin)
        layout.addLayout(rot_layout)

        z_layout = QHBoxLayout()
        z_layout.addWidget(QLabel("Z-Order"))
        z_layout.addWidget(self.z_spin)
        layout.addLayout(z_layout)

        attach_row1 = QHBoxLayout()
        attach_row1.addWidget(QLabel("Lier à"))
        attach_row1.addWidget(self.attach_puppet_combo)
        attach_row1.addWidget(self.attach_member_combo)
        layout.addLayout(attach_row1)

        attach_row2 = QHBoxLayout()
        attach_row2.addWidget(self.attach_btn)
        attach_row2.addWidget(self.detach_btn)
        layout.addLayout(attach_row2)
        # Pas d'étiquette d'état texte (considérée inutile)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.duplicate_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

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
            gi = self.main_window.graphics_items.get(name)
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
            scale = self.main_window.puppet_scales.get(name, 1.0)
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
                item = self.main_window.graphics_items.get(name)
                if item:
                    item.setScale(value)
        else:
            old = self.main_window.puppet_scales.get(name, 1.0)
            if value <= 0:
                return
            ratio = value / old if old else value
            self.main_window.puppet_scales[name] = value
            self.main_window.scale_puppet(name, ratio)

    def _on_delete_clicked(self):
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            # Suppression temporelle: à partir de la frame courante
            self.main_window.delete_object_from_current_frame(name)
        else:
            self.main_window.delete_puppet(name)
        self.refresh()

    def _on_duplicate_clicked(self):
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            self.main_window.duplicate_object(name)
        else:
            self.main_window.duplicate_puppet(name)
        self.refresh()

    def _on_rotation_changed(self, value: float):
        typ, name = self._current_info()
        if typ != "object" or not name:
            return
        obj = self.main_window.scene_model.objects.get(name)
        item = self.main_window.graphics_items.get(name)
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
        item = self.main_window.graphics_items.get(name)
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
            self.main_window.attach_object_to_member(name, puppet, member)
            self._on_item_changed(self.list_widget.currentItem(), None)

    def _on_detach_clicked(self):
        typ, name = self._current_info()
        if typ != "object" or not name:
            return
        self.main_window.detach_object(name)
        self._on_item_changed(self.list_widget.currentItem(), None)

    # --- Helpers ---
    def _attached_state_for_frame(self, obj_name: str):
        """Retourne (puppet_name, member_name) attachés à la frame courante, sinon (None, None)."""
        mw = self.main_window
        idx = mw.scene_model.current_frame
        # Chercher le dernier keyframe <= idx qui contient l'objet
        si = sorted(mw.scene_model.keyframes.keys())
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
