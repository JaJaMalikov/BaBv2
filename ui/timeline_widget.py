
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSlider,
    QSpinBox, QStyleOptionSlider, QStyle, QLabel
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor

class TimelineWidget(QWidget):
    """
    Un widget pour la timeline qui affiche les frames et les keyframes.
    """
    frameChanged = Signal(int)
    addKeyframeClicked = Signal(int)
    deleteKeyframeClicked = Signal(int)
    playClicked = Signal()
    pauseClicked = Signal()
    fpsChanged = Signal(int)
    rangeChanged = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Barre de contrôles ---
        controls_layout = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.setCheckable(True)
        self.play_btn.clicked.connect(self._on_play_clicked)
        controls_layout.addWidget(self.play_btn)

        self.add_keyframe_btn = QPushButton("+ Keyframe")
        self.add_keyframe_btn.clicked.connect(self._on_add_keyframe_clicked)
        controls_layout.addWidget(self.add_keyframe_btn)

        self.delete_keyframe_btn = QPushButton("- Keyframe")
        self.delete_keyframe_btn.clicked.connect(self._on_delete_keyframe_clicked)
        self.delete_keyframe_btn.setEnabled(False)
        controls_layout.addWidget(self.delete_keyframe_btn)

        controls_layout.addStretch()

        # --- Contrôles de lecture ---
        playback_controls_layout = QHBoxLayout()
        playback_controls_layout.addWidget(QLabel("Frame:"))
        self.frame_spinbox = QSpinBox()
        self.frame_spinbox.setRange(0, 9999)
        self.frame_spinbox.valueChanged.connect(self._on_spinbox_changed)
        playback_controls_layout.addWidget(self.frame_spinbox)

        playback_controls_layout.addWidget(QLabel("  Start:"))
        self.start_frame_spinbox = QSpinBox()
        self.start_frame_spinbox.setRange(0, 9999)
        self.start_frame_spinbox.valueChanged.connect(self._on_range_changed)
        playback_controls_layout.addWidget(self.start_frame_spinbox)

        playback_controls_layout.addWidget(QLabel("End:"))
        self.end_frame_spinbox = QSpinBox()
        self.end_frame_spinbox.setRange(0, 9999)
        self.end_frame_spinbox.setValue(100)
        self.end_frame_spinbox.valueChanged.connect(self._on_range_changed)
        playback_controls_layout.addWidget(self.end_frame_spinbox)

        playback_controls_layout.addWidget(QLabel("  FPS:"))
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 120)
        self.fps_spinbox.setValue(24)
        self.fps_spinbox.valueChanged.connect(self.fpsChanged)
        playback_controls_layout.addWidget(self.fps_spinbox)

        main_layout.addLayout(controls_layout)
        main_layout.addLayout(playback_controls_layout)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.valueChanged.connect(self._on_slider_changed)
        main_layout.addWidget(self.slider)

        self._keyframes = set()

    def set_total_frames(self, num_frames):
        self.slider.setRange(0, num_frames)
        self.end_frame_spinbox.setValue(num_frames)

    def set_current_frame(self, frame_index):
        if self.slider.value() != frame_index:
            self.slider.setValue(frame_index)
        if self.frame_spinbox.value() != frame_index:
            self.frame_spinbox.setValue(frame_index)
        self.delete_keyframe_btn.setEnabled(frame_index in self._keyframes)

    def add_keyframe_marker(self, frame_index):
        self._keyframes.add(frame_index)
        self.update()
        self.delete_keyframe_btn.setEnabled(self.slider.value() in self._keyframes)

    def remove_keyframe_marker(self, frame_index):
        self._keyframes.discard(frame_index)
        self.update()
        self.delete_keyframe_btn.setEnabled(self.slider.value() in self._keyframes)

    def clear_keyframes(self):
        self._keyframes.clear()
        self.update()
        self.delete_keyframe_btn.setEnabled(False)

    def _on_slider_changed(self, value):
        self.set_current_frame(value)
        self.frameChanged.emit(value)

    def _on_spinbox_changed(self, value):
        self.set_current_frame(value)
        self.frameChanged.emit(value)

    def _on_add_keyframe_clicked(self):
        current_frame = self.slider.value()
        self.addKeyframeClicked.emit(current_frame)

    def _on_delete_keyframe_clicked(self):
        current_frame = self.slider.value()
        self.deleteKeyframeClicked.emit(current_frame)

    def _on_play_clicked(self, checked):
        if checked:
            self.play_btn.setText("Pause")
            self.playClicked.emit()
        else:
            self.play_btn.setText("Play")
            self.pauseClicked.emit()

    def _on_range_changed(self):
        start = self.start_frame_spinbox.value()
        end = self.end_frame_spinbox.value()
        if start > end:
            self.start_frame_spinbox.setValue(end)
            start = end
        self.slider.setRange(start, end)
        self.rangeChanged.emit(start, end)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        opt = QStyleOptionSlider()
        self.slider.initStyleOption(opt)
        groove_rect = self.slider.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        
        painter.setPen(QColor("#ffc107"))
        painter.setBrush(QColor("#ffc107"))

        for frame in self._keyframes:
            x = self._get_x_for_frame(frame, groove_rect)
            if x is not None:
                marker_rect = QRect(x - 2, groove_rect.center().y() - 4, 4, 8)
                painter.drawRect(marker_rect)

    def _get_x_for_frame(self, frame, groove_rect):
        if self.slider.maximum() <= self.slider.minimum():
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
    window.resize(800, 200)
    window.show()
    sys.exit(app.exec())
