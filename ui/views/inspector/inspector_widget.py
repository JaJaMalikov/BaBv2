"""Inspector panel to list puppets/objects and edit selected object properties.

This widget emits no external signals; it directly calls methods on MainWindow
to manipulate the scene model and graphics items.
"""

import logging

from PySide6.QtWidgets import (
    QWidget,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QDoubleSpinBox,
    QComboBox,
    QToolButton,
    QFormLayout,
    QFrame,
    QLabel,
    QPushButton,
    QColorDialog,
    QSpinBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QColor

from ui.icons import get_icon
from ui.object_item import LightItem


class InspectorWidget(QWidget):
    """Inspector to manage scene objects and puppets."""

    def __init__(self, main_window):
        """Initializes the inspector widget."""
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
        self.attach_btn.setIcon(get_icon("link"))
        self.attach_btn.setToolTip("Lier l'objet au membre")
        self.detach_btn = QToolButton()
        self.detach_btn.setIcon(get_icon("link_off"))
        self.detach_btn.setToolTip("Détacher l'objet")

        self.duplicate_btn = QToolButton()
        self.duplicate_btn.setIcon(get_icon("duplicate"))
        self.duplicate_btn.setToolTip("Dupliquer")
        self.delete_btn = QToolButton()
        self.delete_btn.setIcon(get_icon("delete"))
        self.delete_btn.setToolTip("Supprimer")

        # Light object properties
        self.light_props_widget = QWidget()
        light_layout = QFormLayout(self.light_props_widget)
        self.light_color_btn = QPushButton("Changer…")
        self.light_angle_spin = QDoubleSpinBox()
        self.light_angle_spin.setRange(1, 180)
        self.light_reach_spin = QDoubleSpinBox()
        self.light_reach_spin.setRange(1, 10000)
        self.light_intensity_spin = QSpinBox()
        self.light_intensity_spin.setRange(0, 255)
        light_layout.addRow("Couleur:", self.light_color_btn)
        light_layout.addRow("Intensité (alpha):", self.light_intensity_spin)
        light_layout.addRow("Angle du cône:", self.light_angle_spin)
        light_layout.addRow("Portée:", self.light_reach_spin)

        # --- LAYOUT ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        main_layout.addWidget(self.list_widget)

        # Properties panel (hidden when nothing is selected)
        self.props_panel = QWidget()
        form_layout = QFormLayout(self.props_panel)
        form_layout.setSpacing(8)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.scale_row = QWidget()
        scale_layout = QHBoxLayout(self.scale_row)
        scale_layout.setContentsMargins(0, 0, 0, 0)
        scale_layout.addWidget(QLabel("Échelle:"))
        scale_layout.addWidget(self.scale_spin)
        form_layout.addRow(self.scale_row)

        form_layout.addRow("Rotation:", self.rot_spin)
        form_layout.addRow("Z-Order:", self.z_spin)

        form_layout.addWidget(self.light_props_widget)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        form_layout.addRow(line)

        # Attachment rows wrapped to allow toggling visibility safely (without hiding entire panel)
        self.attach_row = QWidget()
        attach_row_layout = QHBoxLayout(self.attach_row)
        attach_row_layout.setContentsMargins(0, 0, 0, 0)
        attach_row_layout.addWidget(QLabel("Attacher à:"))
        attach_row_layout.addWidget(self.attach_puppet_combo)
        form_layout.addRow(self.attach_row)

        self.member_row = QWidget()
        member_row_layout = QHBoxLayout(self.member_row)
        member_row_layout.setContentsMargins(0, 0, 0, 0)
        member_row_layout.addWidget(QLabel("Membre:"))
        member_row_layout.addWidget(self.attach_member_combo)
        form_layout.addRow(self.member_row)

        attach_actions_layout = QHBoxLayout()
        attach_actions_layout.addStretch()
        attach_actions_layout.addWidget(self.attach_btn)
        attach_actions_layout.addWidget(self.detach_btn)
        self.attach_actions_row = QWidget()
        self.attach_actions_row.setLayout(attach_actions_layout)
        form_layout.addRow(self.attach_actions_row)

        # Variants section (only visible for puppets with defined slots)
        self.variants_panel = QWidget()
        self.variants_layout = QFormLayout(self.variants_panel)
        self.variants_layout.setSpacing(6)
        self.variants_layout.setLabelAlignment(Qt.AlignRight)
        self.variant_combos: dict[str, QComboBox] = {}
        form_layout.addRow(QLabel("Variants:"), self.variants_panel)

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

        main_layout.addWidget(self.props_panel)
        self.props_panel.setVisible(False)

        # --- CONNECTIONS ---
        self.list_widget.currentItemChanged.connect(self._on_item_changed)
        self.scale_spin.valueChanged.connect(self._on_scale_changed)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.duplicate_btn.clicked.connect(self._on_duplicate_clicked)
        self.rot_spin.valueChanged.connect(self._on_rotation_changed)
        self.z_spin.valueChanged.connect(self._on_z_changed)
        self.attach_puppet_combo.currentTextChanged.connect(
            self._on_attach_puppet_changed
        )
        self.attach_btn.clicked.connect(self._on_attach_clicked)
        self.detach_btn.clicked.connect(self._on_detach_clicked)

        # Light property connections
        self.light_color_btn.clicked.connect(self._on_light_color_clicked)
        self.light_angle_spin.valueChanged.connect(self._on_light_props_changed)
        self.light_reach_spin.valueChanged.connect(self._on_light_props_changed)
        self.light_intensity_spin.valueChanged.connect(self._on_light_props_changed)

        self.refresh()

    def _on_light_color_clicked(self):
        typ, name = self._current_info()
        if not (typ == "object" and name):
            return
        obj = self.main_window.scene_model.objects.get(name)
        if not obj or obj.obj_type != "light":
            return

        initial_color = QColor(obj.color or "#FFFFE0")
        new_color = QColorDialog.getColor(
            initial_color, self, "Choisir une couleur pour la lumière"
        )

        if new_color.isValid():
            # Preserve alpha from intensity spin
            alpha = self.light_intensity_spin.value()
            new_color.setAlpha(alpha)
            obj.color = new_color.name(QColor.HexArgb)
            self._on_light_props_changed()  # Trigger update

    def _on_light_props_changed(self):
        typ, name = self._current_info()
        if not (typ == "object" and name):
            return
        obj = self.main_window.scene_model.objects.get(name)
        item = self.main_window.object_manager.graphics_items.get(name)
        if not obj or obj.obj_type != "light" or not isinstance(item, LightItem):
            return

        # Update model from UI
        obj.cone_angle = self.light_angle_spin.value()
        obj.cone_reach = self.light_reach_spin.value()

        new_color = QColor(obj.color or "#FFFFE0")
        new_color.setAlpha(self.light_intensity_spin.value())
        obj.color = new_color.name(QColor.HexArgb)

        # Update graphics item
        item.set_light_properties(new_color, obj.cone_angle, obj.cone_reach)

    # --- Variants helpers ---
    def _current_variant_for_slot(self, puppet_name: str, slot: str) -> str | None:
        """Return the active variant for a slot at the current frame (or default)."""
        mw = self.main_window
        puppet = mw.scene_model.puppets.get(puppet_name)
        if not puppet:
            return None
        candidates = getattr(puppet, "variants", {}).get(slot, [])
        # Resolve from keyframes
        idx = mw.scene_model.current_frame
        si = sorted(mw.scene_model.keyframes.keys())
        last_kf = next((i for i in reversed(si) if i <= idx), None)
        if last_kf is not None:
            vmap = (
                mw.scene_model.keyframes[last_kf]
                .puppets.get(puppet_name, {})
                .get("_variants", {})
            )
            if isinstance(vmap, dict):
                val = vmap.get(slot)
                if isinstance(val, str) and val in candidates:
                    return val
        # Fallback to currently visible piece in scene
        for cand in candidates:
            gi = mw.object_manager.graphics_items.get(f"{puppet_name}:{cand}")
            try:
                if gi and gi.isVisible():
                    return cand
            except RuntimeError:
                continue
        return candidates[0] if candidates else None

    def _rebuild_variant_rows(self, puppet_name: str) -> None:
        """Build or refresh variant selection rows for the selected puppet."""
        puppet = self.main_window.scene_model.puppets.get(puppet_name)
        # Clear existing rows
        for i in reversed(range(self.variants_layout.count())):
            item = self.variants_layout.itemAt(i)
            w = item.widget()
            if w:
                w.deleteLater()
        self.variant_combos.clear()
        slots = list(getattr(puppet, "variants", {}).keys()) if puppet else []
        self.variants_panel.setVisible(bool(slots))
        for slot in sorted(slots):
            combo = QComboBox()
            options = getattr(puppet, "variants", {}).get(slot, [])
            combo.addItems(options)
            current = self._current_variant_for_slot(puppet_name, slot)
            if current:
                idx = combo.findText(current)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            # Connect change
            # Lier le nom du slot et du pantin dans la closure (évite la capture tardive)
            combo.currentTextChanged.connect(
                lambda s, slot_name=slot, puppet=puppet_name: self.main_window.scene_controller.set_member_variant(
                    puppet, slot_name, s
                )
            )
            self.variant_combos[slot] = combo
            self.variants_layout.addRow(f"{slot}:", combo)

    def refresh(self) -> None:
        """Refresh the list from the scene model."""
        self.list_widget.clear()
        model = self.main_window.scene_model
        for name in sorted(model.puppets.keys()):
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, ("puppet", name))
            self.list_widget.addItem(item)
        for name in sorted(model.objects.keys()):
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, ("object", name))
            # Small visual indicator if attached at current frame
            pu, me = self._attached_state_for_frame(name)
            if pu and me:
                item.setIcon(get_icon("link"))
            self.list_widget.addItem(item)
        self._refresh_attach_puppet_combo()
        # Ensure icons reflect current frame state
        self._update_list_attachment_icons()
        # Hide props when nothing selected
        self.props_panel.setVisible(self.list_widget.currentItem() is not None)

    # --- Callbacks ---
    def _current_info(self):
        """Returns the type and name of the currently selected item."""
        item = self.list_widget.currentItem()
        if not item:
            return None, None
        return item.data(Qt.UserRole)

    def _on_item_changed(self, current, previous):
        """Handles the selection change in the list widget.

        Use the 'current' item provided by the signal to avoid timing issues
        where QListWidget.currentItem() may still be None.
        """
        if current is None:
            self.props_panel.setVisible(False)
            return
        data = current.data(Qt.UserRole)
        typ, name = data if data else (None, None)
        if not name:
            self.props_panel.setVisible(False)
            return

        self.props_panel.setVisible(True)
        obj = self.main_window.scene_model.objects.get(name)
        is_light = typ == "object" and obj and obj.obj_type == "light"

        self.light_props_widget.setVisible(is_light)
        self.scale_row.setVisible(not is_light)
        self.variants_panel.setVisible(typ == "puppet")
        is_object = typ == "object"
        # Toggle only the attachment-related rows; do not hide the whole panel
        if hasattr(self, "attach_row"):
            self.attach_row.setVisible(is_object)
        if hasattr(self, "member_row"):
            self.member_row.setVisible(is_object)
        if hasattr(self, "attach_actions_row"):
            self.attach_actions_row.setVisible(is_object)

        if typ == "object":
            if is_light and obj:
                self.light_angle_spin.setValue(obj.cone_angle or 45.0)
                self.light_reach_spin.setValue(obj.cone_reach or 500.0)
                color = QColor(obj.color or "#FFFFE0")
                self.light_intensity_spin.setValue(color.alpha())
            else:
                self.scale_spin.setValue(obj.scale if obj else 1.0)
            self.rot_spin.setValue(obj.rotation if obj else 0.0)
            self.z_spin.setValue(getattr(obj, "z", 0))

            # Reflect selection in the scene view
            try:
                for it in self.main_window.scene.selectedItems():
                    it.setSelected(False)
                gi = self.main_window.object_manager.graphics_items.get(name)
                if gi and gi.isVisible():
                    gi.setSelected(True)
            except Exception:
                pass

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
        else:  # Puppet
            self.scale_spin.setValue(
                self.main_window.object_manager.puppet_scales.get(name, 1.0)
            )
            self.rot_spin.setValue(
                self.main_window.scene_controller.get_puppet_rotation(name)
            )
            self.z_spin.setValue(
                self.main_window.object_manager.puppet_z_offsets.get(name, 0)
            )
            self._rebuild_variant_rows(name)

    def _on_scale_changed(self, value: float) -> None:
        """Handles the scale change of the selected item."""
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            # Route model mutation via controller; keep immediate visual update
            self.main_window.scene_controller.set_object_scale(name, float(value))
            item = self.main_window.object_manager.graphics_items.get(name)
            if item:
                item.setScale(value)
        else:
            old = self.main_window.object_manager.puppet_scales.get(name, 1.0)
            if value <= 0:
                return
            ratio = value / old if old else value
            self.main_window.object_manager.puppet_scales[name] = value
            self.main_window.scene_controller.scale_puppet(name, ratio)

    def _on_delete_clicked(self) -> None:
        """Handles the deletion of the selected item."""
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            self.main_window.scene_controller.delete_object(name)
        else:
            self.main_window.scene_controller.delete_puppet(name)
        self.refresh()

    def _on_duplicate_clicked(self) -> None:
        """Handles the duplication of the selected item."""
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            self.main_window.scene_controller.duplicate_object(name)
        else:
            self.main_window.scene_controller.duplicate_puppet(name)
        self.refresh()

    def _on_rotation_changed(self, value: float) -> None:
        """Handles the rotation change of the selected item."""
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            item = self.main_window.object_manager.graphics_items.get(name)
            # Route model mutation via controller; keep immediate visual update
            self.main_window.scene_controller.set_object_rotation(name, float(value))
            if item:
                try:
                    item.setTransformOriginPoint(item.boundingRect().center())
                except RuntimeError as e:
                    logging.debug("Failed to set transform origin in inspector: %s", e)
                item.setRotation(value)
        else:
            # Rotation du pantin entier (autour du pivot de la pièce racine)
            self.main_window.scene_controller.set_puppet_rotation(name, value)

    def _on_z_changed(self, value: float) -> None:
        """Handles the z-order change of the selected item."""
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            item = self.main_window.object_manager.graphics_items.get(name)
            # Route model mutation via controller; keep immediate visual update
            self.main_window.scene_controller.set_object_z(name, int(value))
            if item:
                item.setZValue(int(value))
        else:
            # Z offset global du pantin (appliqué à toutes les pièces)
            self.main_window.scene_controller.set_puppet_z_offset(name, int(value))

    def _refresh_attach_puppet_combo(self) -> None:
        """Refreshes the puppet attachment combo box."""
        self.attach_puppet_combo.blockSignals(True)
        self.attach_puppet_combo.clear()
        self.attach_puppet_combo.addItem("")
        for name in sorted(self.main_window.scene_model.puppets.keys()):
            self.attach_puppet_combo.addItem(name)
        self.attach_puppet_combo.blockSignals(False)
        self._refresh_attach_member_combo()

    def _refresh_attach_member_combo(self) -> None:
        """Refreshes the member attachment combo box."""
        puppet = self.attach_puppet_combo.currentText()
        self.attach_member_combo.clear()
        if puppet and puppet in self.main_window.scene_model.puppets:
            members = sorted(
                self.main_window.scene_model.puppets[puppet].members.keys()
            )
            self.attach_member_combo.addItems(members)

    def _on_attach_puppet_changed(self, _):
        """Handles the change of the selected puppet for attachment."""
        self._refresh_attach_member_combo()

    def _on_attach_clicked(self) -> None:
        """Handles the attachment of the selected object to a puppet member."""
        typ, name = self._current_info()
        if typ != "object" or not name:
            return
        puppet = self.attach_puppet_combo.currentText()
        member = self.attach_member_combo.currentText()
        if puppet and member:
            self.main_window.scene_controller.attach_object_to_member(
                name, puppet, member
            )
            self._on_item_changed(self.list_widget.currentItem(), None)
            self._update_list_attachment_icons()

    def _on_detach_clicked(self) -> None:
        """Handles the detachment of the selected object."""
        typ, name = self._current_info()
        if typ != "object" or not name:
            return
        self.main_window.scene_controller.detach_object(name)
        self._on_item_changed(self.list_widget.currentItem(), None)
        self._update_list_attachment_icons()

    # --- Helpers ---
    def _attached_state_for_frame(self, obj_name: str):
        """Retourne (puppet_name, member_name) à la frame courante, sinon (None, None).

        Respecte la même politique de visibilité que la scène: si le keyframe le plus
        récent ≤ frame ne contient pas l'objet, on considère l'objet masqué/détaché.
        """
        mw = self.main_window
        idx = mw.scene_model.current_frame
        si = sorted(mw.scene_model.keyframes.keys())
        last_kf = next((i for i in reversed(si) if i <= idx), None)
        if (
            last_kf is not None
            and obj_name not in mw.scene_model.keyframes[last_kf].objects
        ):
            return (None, None)
        prev = next(
            (
                i
                for i in reversed(si)
                if i <= idx and obj_name in mw.scene_model.keyframes[i].objects
            ),
            None,
        )
        if prev is None:
            obj = mw.scene_model.objects.get(obj_name)
            return obj.attached_to if obj and obj.attached_to else (None, None)
        st = mw.scene_model.keyframes[prev].objects.get(obj_name, {})
        attached = st.get("attached_to")
        if attached:
            try:
                pu, me = attached
                return pu, me
            except ValueError as e:
                logging.debug("Invalid 'attached_to' format in inspector: %s", e)
                return (None, None)
        return (None, None)

    def sync_with_frame(self) -> None:
        """À appeler quand la frame courante change.

        Met à jour l'état d'attache affiché sans modifier la sélection de scène.
        Évite de réimposer la sélection de l'objet dans la scène à chaque changement de frame.
        """
        cur = self.list_widget.currentItem()
        if cur is None:
            return
        typ, name = cur.data(Qt.UserRole)
        # Rafraîchir uniquement les combos d'attache pour les objets
        if typ == "object" and name:
            self._refresh_attach_puppet_combo()
            pu, me = self._attached_state_for_frame(name)
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
        # Sync variant combos when puppet is selected
        if typ == "puppet" and name and self.variants_panel.isVisible():
            puppet = self.main_window.scene_model.puppets.get(name)
            for slot, combo in list(self.variant_combos.items()):
                if slot not in getattr(puppet, "variants", {}):
                    continue
                cur = self._current_variant_for_slot(name, slot)
                if cur is None:
                    continue
                idx = combo.findText(cur)
                if idx >= 0 and combo.currentIndex() != idx:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(idx)
                    combo.blockSignals(False)
        # Update icons for all objects to reflect current frame
        self._update_list_attachment_icons()

    def _update_list_attachment_icons(self) -> None:
        """Set a small link icon on object items that are attached at the current frame."""
        for i in range(self.list_widget.count()):
            it: QListWidgetItem = self.list_widget.item(i)
            typ, nm = it.data(Qt.UserRole)
            if typ != "object":
                continue
            pu, me = self._attached_state_for_frame(nm)
            if pu and me:
                it.setIcon(get_icon("link"))
            else:
                # Clear icon to keep list clean when not attached
                it.setIcon(QIcon())
