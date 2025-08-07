
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSlider,
     QSpinBox, QStyleOptionSlider, QStyle
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor

class TimelineWidget(QWidget):
    """
    Un widget pour la timeline qui affiche les frames et les keyframes.
    """
    frameChanged = Signal(int)
    addKeyframeClicked = Signal(int)
    playClicked = Signal()
    pauseClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Barre de contrôles ---
        controls_layout = QHBoxLayout()
        
        # Bouton Play/Pause
        self.play_btn = QPushButton("Play")
        self.play_btn.setCheckable(True)
        self.play_btn.clicked.connect(self._on_play_clicked)
        controls_layout.addWidget(self.play_btn)

        # Bouton "Ajouter Keyframe"
        self.add_keyframe_btn = QPushButton("+ Keyframe")
        self.add_keyframe_btn.clicked.connect(self._on_add_keyframe_clicked)
        controls_layout.addWidget(self.add_keyframe_btn)

        # Affichage de la frame actuelle
        self.frame_spinbox = QSpinBox()
        self.frame_spinbox.setRange(0, 9999)
        self.frame_spinbox.valueChanged.connect(self._on_spinbox_changed)
        controls_layout.addWidget(self.frame_spinbox)
        
        controls_layout.addStretch()

        main_layout.addLayout(controls_layout)

        # --- Slider de la timeline ---
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)  # 100 frames par défaut
        self.slider.valueChanged.connect(self._on_slider_changed)
        main_layout.addWidget(self.slider)

        # --- Variables d'état ---
        self._keyframes = set()

    def set_total_frames(self, num_frames):
        """Définit le nombre total de frames sur la timeline."""
        self.slider.setRange(0, num_frames)

    def set_current_frame(self, frame_index):
        """Met à jour la position du curseur et du spinbox."""
        if self.slider.value() != frame_index:
            self.slider.setValue(frame_index)
        if self.frame_spinbox.value() != frame_index:
            self.frame_spinbox.setValue(frame_index)

    def add_keyframe_marker(self, frame_index):
        """Ajoute un marqueur visuel pour une keyframe."""
        self._keyframes.add(frame_index)
        self.update() # Redessine le widget

    def clear_keyframes(self):
        """Supprime tous les marqueurs de keyframes."""
        self._keyframes.clear()
        self.update()

    def _on_slider_changed(self, value):
        self.set_current_frame(value)
        self.frameChanged.emit(value)

    def _on_spinbox_changed(self, value):
        self.set_current_frame(value)
        self.frameChanged.emit(value)

    def _on_add_keyframe_clicked(self):
        current_frame = self.slider.value()
        self.addKeyframeClicked.emit(current_frame)

    def _on_play_clicked(self, checked):
        if checked:
            self.play_btn.setText("Pause")
            self.playClicked.emit()
        else:
            self.play_btn.setText("Play")
            self.pauseClicked.emit()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        opt = QStyleOptionSlider()
        self.slider.initStyleOption(opt)
        groove_rect = self.slider.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        
        # Dessiner les marqueurs de keyframes
        painter.setPen(QColor("#ffc107")) # Jaune ambré
        painter.setBrush(QColor("#ffc107"))

        for frame in self._keyframes:
            x = self._get_x_for_frame(frame, groove_rect)
            if x is not None:
                marker_rect = QRect(x - 2, groove_rect.center().y() - 4, 4, 8)
                painter.drawRect(marker_rect)

    def _get_x_for_frame(self, frame, groove_rect):
        if self.slider.maximum() == self.slider.minimum():
            return None
        
        slider_range = self.slider.maximum() - self.slider.minimum()
        slider_pos = (frame - self.slider.minimum()) / slider_range
        
        return groove_rect.left() + groove_rect.width() * slider_pos


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    timeline = TimelineWidget()
    timeline.add_keyframe_marker(10)
    timeline.add_keyframe_marker(25)
    timeline.add_keyframe_marker(50)
    timeline.add_keyframe_marker(90)
    layout.addWidget(timeline)
    window.resize(800, 150)
    window.show()
    sys.exit(app.exec())
