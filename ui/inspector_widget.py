from PySide6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QComboBox, QToolButton
)
from PySide6.QtCore import Qt
from ui.icons import icon_delete, icon_duplicate, icon_link, icon_link_off
from ui.styles import BUTTON_STYLE

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
        self.duplicate_btn = QToolButton()
        self.duplicate_btn.setIcon(icon_duplicate())
        self.duplicate_btn.setToolTip("Dupliquer")
        self.duplicate_btn.setStyleSheet(BUTTON_STYLE)

        self.delete_btn = QToolButton()
        self.delete_btn.setIcon(icon_delete())
        self.delete_btn.setToolTip("Supprimer")
        self.delete_btn.setStyleSheet(BUTTON_STYLE)
        self.attach_puppet_combo = QComboBox()
        self.attach_member_combo = QComboBox()
        self.attach_btn = QToolButton()
        self.attach_btn.setIcon(icon_link())
        self.attach_btn.setToolTip("Lier l'objet au membre")
        self.attach_btn.setStyleSheet(BUTTON_STYLE)

        self.detach_btn = QToolButton()
        self.detach_btn.setIcon(icon_link_off())
        self.detach_btn.setToolTip("Détacher l'objet")
        self.detach_btn.setStyleSheet(BUTTON_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self.list_widget)

        # Transform card
        transform_card = QWidget(self)
        transform_card.setProperty("role", "card")
        tlay = QVBoxLayout(transform_card); tlay.setContentsMargins(8, 8, 8, 8); tlay.setSpacing(6)
        lbl_t = QLabel("Transformations"); lbl_t.setProperty("role", "section-title"); tlay.addWidget(lbl_t)
        row1 = QHBoxLayout(); row1.addWidget(QLabel("Échelle")); row1.addWidget(self.scale_spin); tlay.addLayout(row1)
        row2 = QHBoxLayout(); row2.addWidget(QLabel("Rotation")); row2.addWidget(self.rot_spin); tlay.addLayout(row2)
        row3 = QHBoxLayout(); row3.addWidget(QLabel("Z-Order")); row3.addWidget(self.z_spin); tlay.addLayout(row3)
        layout.addWidget(transform_card)

        # Attachment card
        attach_card = QWidget(self)
        attach_card.setProperty("role", "card")
        alay = QVBoxLayout(attach_card); alay.setContentsMargins(8, 8, 8, 8); alay.setSpacing(6)
        lbl_a = QLabel("Attachement"); lbl_a.setProperty("role", "section-title"); alay.addWidget(lbl_a)
        ar1 = QHBoxLayout(); ar1.addWidget(QLabel("Pantin")); ar1.addWidget(self.attach_puppet_combo); alay.addLayout(ar1)
        ar2 = QHBoxLayout(); ar2.addWidget(QLabel("Membre")); ar2.addWidget(self.attach_member_combo); alay.addLayout(ar2)
        ar3 = QHBoxLayout(); ar3.addWidget(self.attach_btn); ar3.addWidget(self.detach_btn); alay.addLayout(ar3)
        layout.addWidget(attach_card)

        # Actions card
        actions_card = QWidget(self)
        actions_card.setProperty("role", "card")
        blay = QHBoxLayout(actions_card); blay.setContentsMargins(8, 8, 8, 8); blay.setSpacing(6)
        blay.addWidget(self.duplicate_btn)
        blay.addWidget(self.delete_btn)
        layout.addWidget(actions_card)

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
