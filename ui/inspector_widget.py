from PySide6.QtWidgets import (
    QWidget,
    QListWidget,
    QVBoxLayout,
    QFormLayout,
    QDoubleSpinBox,
    QPushButton,
    QHBoxLayout,
    QListWidgetItem,
)
from PySide6.QtCore import Qt


class InspectorWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        form = QFormLayout()
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 10.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.valueChanged.connect(self._scale_changed)
        form.addRow("Scale", self.scale_spin)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.duplicate_btn = QPushButton("Dupliquer")
        self.delete_btn = QPushButton("Supprimer")
        btn_layout.addWidget(self.duplicate_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        self.list_widget.currentItemChanged.connect(self._selection_changed)
        self.delete_btn.clicked.connect(self._delete_current)
        self.duplicate_btn.clicked.connect(self._duplicate_current)

        self.scale_spin.setEnabled(False)

    def refresh(self):
        self.list_widget.clear()
        for name in sorted(self.main_window.scene_model.puppets.keys()):
            item = QListWidgetItem(f"Puppet: {name}")
            item.setData(Qt.UserRole, ("puppet", name))
            self.list_widget.addItem(item)
        for name in sorted(self.main_window.scene_model.objects.keys()):
            item = QListWidgetItem(f"Object: {name}")
            item.setData(Qt.UserRole, ("object", name))
            self.list_widget.addItem(item)

    def _selection_changed(self, current, previous):
        if not current:
            self.scale_spin.setEnabled(False)
            return
        typ, name = current.data(Qt.UserRole)
        self.scale_spin.setEnabled(True)
        self.scale_spin.blockSignals(True)
        if typ == "puppet":
            puppet = self.main_window.scene_model.puppets.get(name)
            scale_val = 1.0
            if puppet:
                for root in puppet.get_root_members():
                    piece = self.main_window.graphics_items.get(f"{name}:{root.name}")
                    if piece:
                        scale_val = piece.scale()
                        break
            self.scale_spin.setValue(scale_val)
        else:
            obj = self.main_window.scene_model.objects.get(name)
            if obj:
                self.scale_spin.setValue(obj.scale)
            else:
                self.scale_spin.setValue(1.0)
        self.scale_spin.blockSignals(False)

    def _scale_changed(self, value):
        item = self.list_widget.currentItem()
        if not item:
            return
        typ, name = item.data(Qt.UserRole)
        if typ == "puppet":
            self.main_window.set_puppet_scale(name, value)
        else:
            self.main_window.set_object_scale(name, value)

    def _delete_current(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        typ, name = item.data(Qt.UserRole)
        if typ == "puppet":
            self.main_window.remove_puppet(name)
        else:
            self.main_window.remove_object(name)

    def _duplicate_current(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        typ, name = item.data(Qt.UserRole)
        if typ == "puppet":
            self.main_window.duplicate_puppet(name)
        else:
            self.main_window.duplicate_object(name)

