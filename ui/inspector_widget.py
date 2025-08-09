from PySide6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton
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
        self.duplicate_btn = QPushButton("Dupliquer")
        self.delete_btn = QPushButton("Supprimer")

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)

        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Échelle"))
        scale_layout.addWidget(self.scale_spin)
        layout.addLayout(scale_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.duplicate_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        self.list_widget.currentItemChanged.connect(self._on_item_changed)
        self.scale_spin.valueChanged.connect(self._on_scale_changed)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.duplicate_btn.clicked.connect(self._on_duplicate_clicked)

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
        else:
            scale = self.main_window.puppet_scales.get(name, 1.0)
        self.scale_spin.blockSignals(True)
        self.scale_spin.setValue(scale)
        self.scale_spin.blockSignals(False)

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
            self.main_window.delete_object(name)
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

