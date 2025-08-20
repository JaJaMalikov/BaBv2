"""Inspector panel to list puppets/objects and edit selected object properties.

DEPRECATION NOTICE (docs/tasks.md §23):
- This widget currently accesses `main_window.scene_model` and
  `main_window.object_manager.graphics_items` directly in several places.
- This is being phased out in favor of a controller facade and a selection model.
- New code should route through controller/facade methods and view adapters.

For now, we keep these direct accesses to avoid breaking tests; they are marked
with TODO(§23) comments where relevant.
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

from ui.icons import icon_delete, icon_duplicate, icon_link, icon_link_off
from ui.object_item import LightItem
from ui.selection_sync import subscribe_model_changed, unsubscribe_model_changed


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
        # Keep a reference for later label lookups when toggling visibility
        self.form_layout = form_layout

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

        form_layout.addRow("Attacher à:", self.attach_puppet_combo)
        form_layout.addRow("Membre:", self.attach_member_combo)
        # Store labels for later visibility toggling
        self.attach_puppet_label = form_layout.labelForField(self.attach_puppet_combo)
        self.attach_member_label = form_layout.labelForField(self.attach_member_combo)

        # Buttons row wrapped in a widget to hide/show easily
        self.attach_actions_widget = QWidget()
        attach_actions_layout = QHBoxLayout(self.attach_actions_widget)
        attach_actions_layout.addStretch()
        attach_actions_layout.addWidget(self.attach_btn)
        attach_actions_layout.addWidget(self.detach_btn)
        form_layout.addRow("", self.attach_actions_widget)
        self.attach_actions_label = form_layout.labelForField(self.attach_actions_widget)

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
        self.attach_puppet_combo.currentTextChanged.connect(self._on_attach_puppet_changed)
        self.attach_btn.clicked.connect(self._on_attach_clicked)
        self.detach_btn.clicked.connect(self._on_detach_clicked)

        # Light property connections
        self.light_color_btn.clicked.connect(self._on_light_color_clicked)
        self.light_angle_spin.valueChanged.connect(self._on_light_props_changed)
        self.light_reach_spin.valueChanged.connect(self._on_light_props_changed)
        self.light_intensity_spin.valueChanged.connect(self._on_light_props_changed)

        self.refresh()

        # Subscribe to model-changed events (docs/tasks.md §4)
        try:
            subscribe_model_changed(self.main_window, self.refresh)
            # Ensure we unsubscribe when this widget is destroyed to avoid stale refs
            self.destroyed.connect(lambda *_: unsubscribe_model_changed(self.main_window, self.refresh))
        except Exception:
            # Non-fatal: inspector still works with direct refresh calls
            pass

    def _on_light_color_clicked(self):
        typ, name = self._current_info()
        if not (typ == "object" and name):
            return
        # Prefer controller/facade: avoid direct model writes
        obj = self.main_window.scene_model.objects.get(name)
        if not obj or obj.obj_type != "light":
            return

        initial_color = QColor(obj.color or "#FFFFE0")
        new_color = QColorDialog.getColor(
            initial_color, self, "Choisir une couleur pour la lumière"
        )

        if new_color.isValid():
            # Preserve alpha from intensity spin and route via controller
            alpha = self.light_intensity_spin.value()
            new_color.setAlpha(alpha)
            self.main_window.object_controller.set_light_properties(
                name,
                new_color.name(QColor.HexArgb),
                float(self.light_angle_spin.value()),
                float(self.light_reach_spin.value()),
            )
            # Refresh UI fields from model state
            self._on_item_changed(self.list_widget.currentItem(), None)

    def _on_light_props_changed(self):
        typ, name = self._current_info()
        if not (typ == "object" and name):
            return
        # Route through controller to update model and visuals
        facade = getattr(self.main_window, "scene_facade", None)
        if not facade:
            return
        info = facade.get_object_info(name)
        if not info or not info.is_light:
            return
        color = QColor(info.light_color or "#FFFFE0")
        color.setAlpha(self.light_intensity_spin.value())
        self.main_window.object_controller.set_light_properties(
            name,
            color.name(QColor.HexArgb),
            float(self.light_angle_spin.value()),
            float(self.light_reach_spin.value()),
        )

    # --- Variants helpers ---
    def _current_variant_for_slot(self, puppet_name: str, slot: str) -> str | None:
        """Return the active variant for a slot at the current frame (or default).

        Prefers controller facade queries to avoid UI touching the model directly
        (docs/tasks.md §3, §8). Falls back to legacy logic if the facade is missing.
        """
        mw = self.main_window
        facade = getattr(mw, "scene_facade", None)
        if facade:
            try:
                return facade.get_current_variant_for_slot(puppet_name, slot)
            except Exception:
                pass
        # Legacy fallback kept for robustness during migration
        puppet = mw.scene_model.puppets.get(puppet_name)
        if not puppet:
            return None
        candidates = getattr(puppet, "variants", {}).get(slot, [])
        idx = mw.scene_model.current_frame
        si = sorted(mw.scene_model.keyframes.keys())
        last_kf = next((i for i in reversed(si) if i <= idx), None)
        if last_kf is not None:
            vmap = mw.scene_model.keyframes[last_kf].puppets.get(puppet_name, {}).get("_variants", {})
            if isinstance(vmap, dict):
                val = vmap.get(slot)
                if isinstance(val, str) and val in candidates:
                    return val
        return candidates[0] if candidates else None

    def _rebuild_variant_rows(self, puppet_name: str) -> None:
        """Build or refresh variant selection rows for the selected puppet.

        Uses SceneFacade for read-only queries to respect MVC boundaries.
        """
        # Clear existing rows
        for i in reversed(range(self.variants_layout.count())):
            item = self.variants_layout.itemAt(i)
            w = item.widget()
            if w:
                w.deleteLater()
        self.variant_combos.clear()

        facade = getattr(self.main_window, "scene_facade", None)
        if facade:
            slots = facade.get_puppet_variant_slots(puppet_name)
        else:
            # Fallback to legacy direct model access during migration
            puppet = self.main_window.scene_model.puppets.get(puppet_name)
            slots = list(getattr(puppet, "variants", {}).keys()) if puppet else []

        self.variants_panel.setVisible(bool(slots))
        for slot in sorted(slots):
            combo = QComboBox()
            if facade:
                options = facade.get_puppet_variant_options(puppet_name, slot)
            else:
                puppet = self.main_window.scene_model.puppets.get(puppet_name)
                options = getattr(puppet, "variants", {}).get(slot, []) if puppet else []
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
        """Refresh the list from the scene via the controller facade."""
        self.list_widget.clear()
        # Puppets
        puppet_names: list[str] = []
        try:
            facade = getattr(self.main_window, "scene_facade", None)
            puppet_names = facade.get_puppet_names() if facade else []
        except Exception:
            puppet_names = []
        if not puppet_names:
            try:
                puppet_names = sorted(self.main_window.scene_model.puppets.keys())
            except Exception:
                puppet_names = []
        for name in puppet_names:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, ("puppet", name))
            self.list_widget.addItem(item)
        # Objects
        object_names: list[str] = []
        try:
            facade = getattr(self.main_window, "scene_facade", None)
            object_names = facade.get_object_names() if facade else []
        except Exception:
            object_names = []
        if not object_names:
            try:
                object_names = sorted(self.main_window.scene_model.objects.keys())
            except Exception:
                object_names = []
        for name in object_names:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, ("object", name))
            # Small visual indicator if attached at current frame
            pu, me = self._attached_state_for_frame(name)
            if pu and me:
                item.setIcon(icon_link())
            self.list_widget.addItem(item)
        self._refresh_attach_puppet_combo()
        # Ensure icons reflect current frame state
        self._update_list_attachment_icons()
        # Hide props when nothing selected
        self.props_panel.setVisible(self.list_widget.currentItem() is not None)

    # --- Callbacks ---
    def _current_info(self):
        """Returns the type and name of the currently selected item.

        Falls back to the last known selection to be resilient to transient
        selection updates triggered by scene highlights.
        """
        item = self.list_widget.currentItem()
        if item:
            info = item.data(Qt.UserRole)
            # Cache for resilience
            try:
                self._last_selection = info
            except Exception:
                pass
            return info
        # Fallback
        return getattr(self, "_last_selection", (None, None))

    def _on_item_changed(self, current, previous):
        """Handles the selection change in the list widget."""
        typ, name = self._current_info()
        if not name:
            self.props_panel.setVisible(False)
            return

        self.props_panel.setVisible(True)
        facade = getattr(self.main_window, "scene_facade", None)
        info = facade.get_object_info(name) if (typ == "object" and facade) else None
        is_light = bool(info and info.is_light)

        self.light_props_widget.setVisible(is_light)
        self.scale_row.setVisible(not is_light)
        self.variants_panel.setVisible(typ == "puppet")
        is_object = typ == "object"
        # Toggle visibility of attachment controls and their labels without hiding the panel
        for widget in (
            self.attach_puppet_combo,
            self.attach_member_combo,
            self.attach_actions_widget,
            self.attach_puppet_label,
            self.attach_member_label,
            self.attach_actions_label,
        ):
            if widget:
                widget.setVisible(is_object)

        if typ == "object":
            if is_light and info:
                self.light_angle_spin.setValue(float(info.light_cone_angle or 45.0))
                self.light_reach_spin.setValue(float(info.light_cone_reach or 500.0))
                color = QColor(info.light_color or "#FFFFE0")
                self.light_intensity_spin.setValue(color.alpha())
            else:
                self.scale_spin.setValue(float(info.scale) if info else 1.0)

            self.rot_spin.setValue(float(info.rotation) if info else 0.0)
            self.z_spin.setValue(int(info.z) if info else 0)

            try:
                # Drive selection via facade (docs/tasks.md §16)
                fac = getattr(self.main_window, "scene_facade", None)
                if fac:
                    fac.select_object(name)
                else:
                    # Fallback: highlight directly during migration
                    from ui.selection_sync import highlight_scene_object
                    highlight_scene_object(self.main_window, name)
            except Exception:
                # Fallback legacy selection direct access
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
            self.scale_spin.setValue(self.main_window.scene_controller.get_puppet_scale(name))
            self.rot_spin.setValue(self.main_window.scene_controller.get_puppet_rotation(name))
            self.z_spin.setValue(self.main_window.scene_controller.get_puppet_z_offset(name))
            self._rebuild_variant_rows(name)

    def _on_scale_changed(self, value: float) -> None:
        """Handles the scale change of the selected item."""
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            # Route via controller (docs/tasks.md §3 & §14)
            self.main_window.object_controller.set_object_scale(name, float(value))
        else:
            if value <= 0:
                return
            # Use controller API to centralize absolute scale changes
            self.main_window.scene_controller.set_puppet_scale(name, float(value))

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
            # Route via controller
            self.main_window.object_controller.set_object_rotation(name, float(value))
        else:
            # Rotation du pantin entier (autour du pivot de la pièce racine)
            self.main_window.scene_controller.set_puppet_rotation(name, value)

    def _on_z_changed(self, value: float) -> None:
        """Handles the z-order change of the selected item."""
        typ, name = self._current_info()
        if not name:
            return
        if typ == "object":
            # Route via controller
            self.main_window.object_controller.set_object_z(name, int(value))
        else:
            # Z offset global du pantin (appliqué à toutes les pièces)
            self.main_window.scene_controller.set_puppet_z_offset(name, int(value))

    def _refresh_attach_puppet_combo(self) -> None:
        """Refreshes the puppet attachment combo box.

        docs/tasks.md §3: query via facade to avoid direct model traversal.
        """
        self.attach_puppet_combo.blockSignals(True)
        self.attach_puppet_combo.clear()
        self.attach_puppet_combo.addItem("")
        try:
            facade = getattr(self.main_window, "scene_facade", None)
            names = facade.get_puppet_names() if facade else []
        except Exception:
            names = []
        if not names:
            # Fallback to legacy model access to keep behavior in edge cases
            try:
                names = sorted(self.main_window.scene_model.puppets.keys())
            except Exception:
                names = []
        for name in names:
            self.attach_puppet_combo.addItem(name)
        self.attach_puppet_combo.blockSignals(False)
        self._refresh_attach_member_combo()

    def _refresh_attach_member_combo(self) -> None:
        """Refreshes the member attachment combo box.

        docs/tasks.md §3: query via facade to avoid direct model traversal.
        """
        puppet = self.attach_puppet_combo.currentText()
        self.attach_member_combo.clear()
        members: list[str] = []
        if puppet:
            try:
                facade = getattr(self.main_window, "scene_facade", None)
                members = facade.get_puppet_member_names(puppet) if facade else []
            except Exception:
                members = []
            if not members:
                # Fallback to legacy model access
                try:
                    if puppet in self.main_window.scene_model.puppets:
                        members = sorted(self.main_window.scene_model.puppets[puppet].members.keys())
                except Exception:
                    members = []
        if members:
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
            self.main_window.scene_controller.attach_object_to_member(name, puppet, member)
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
        facade = getattr(self.main_window, "scene_facade", None)
        if not facade:
            return (None, None)
        try:
            return facade.get_object_attachment_at_current_frame(obj_name)
        except Exception as e:
            logging.debug("Failed to resolve attachment via facade: %s", e)
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
                it.setIcon(icon_link())
            else:
                # Clear icon to keep list clean when not attached
                it.setIcon(QIcon())
