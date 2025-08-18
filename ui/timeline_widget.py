"""Module for the timeline widget, which provides a user interface for controlling animation playback."""

from __future__ import annotations

import math
from typing import Optional, Set, List

from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QRect, QEvent
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QMouseEvent,
    QWheelEvent,
    QKeyEvent,
    QAction,
    QPolygonF,
)
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QSlider,
    QSpinBox,
    QLabel,
    QMenu,
    QToolButton,
    QSpacerItem,
    QSizePolicy,
)

# --- Constants ---
RULER_H: int = 24
TRACK_H: int = 28
PLAYHEAD_W: int = 2
TOOLBAR_H: int = 30


def _c(val: str, default: str) -> QColor:
    try:
        s = QSettings("JaJa", "Macronotron")
        v = s.value(f"timeline/{val}")
        return QColor(str(v)) if v else QColor(default)
    except Exception:
        return QColor(default)


def _alpha(default: int) -> int:
    try:
        s = QSettings("JaJa", "Macronotron")
        v = s.value("timeline/inout_alpha")
        return int(v) if v is not None else default
    except Exception:
        return default


DIAMOND_W: int = 10
DIAMOND_H: int = 10


class TimelineWidget(QWidget):
    """Lightweight timeline widget.

    Emits signals for frame changes, play/pause/stop, range and FPS changes,
    and exposes helpers to add/remove keyframe markers. The widget does not
    mutate the scene model; MainWindow/PlaybackHandler should handle logic.
    """

    frameChanged = Signal(int)
    addKeyframeClicked = Signal(int)
    deleteKeyframeClicked = Signal(int)
    copyKeyframeClicked = Signal(int)
    pasteKeyframeClicked = Signal(int)
    playClicked = Signal()
    pauseClicked = Signal()
    stopClicked = Signal()
    loopToggled = Signal(bool)
    fpsChanged = Signal(int)
    rangeChanged = Signal(int, int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initializes the TimelineWidget.

        Args:
            parent: The parent widget.
        """
        super().__init__(parent)

        self._kfs: Set[int] = set()
        self._start: int = 0
        self._end: int = 100
        self._fps: int = 24
        self._current: int = 0
        self.loop_enabled: bool = True

        self._px_per_frame: float = 10.0
        self._min_ppf: float = 1.0
        self._max_ppf: float = 50.0
        self._scroll_frames: float = 0.0
        self._hover_kf: Optional[int] = None
        self._dragging_playhead: bool = False

        self.toolbar: QWidget = QWidget(self)
        self.toolbar.setFixedHeight(TOOLBAR_H)
        bar: QHBoxLayout = QHBoxLayout(self.toolbar)
        bar.setContentsMargins(4, 0, 4, 0)
        bar.setSpacing(4)

        self.play_btn: QToolButton = QToolButton()
        self.play_btn.setText("⏵")
        self.play_btn.setCheckable(True)
        self.play_btn.clicked.connect(self._on_play_clicked)

        self.stop_btn: QToolButton = QToolButton()
        self.stop_btn.setText("■")
        self.stop_btn.setToolTip("Stop and go to start")
        self.stop_btn.clicked.connect(self._on_stop_clicked)

        self.prev_kf_btn: QToolButton = QToolButton()
        self.prev_kf_btn.setText("|◀")
        self.prev_kf_btn.setToolTip("Previous keyframe")
        self.prev_kf_btn.clicked.connect(self._jump_prev_kf)

        self.next_kf_btn: QToolButton = QToolButton()
        self.next_kf_btn.setText("▶|")
        self.next_kf_btn.setToolTip("Next keyframe")
        self.next_kf_btn.clicked.connect(self._jump_next_kf)

        self.loop_btn: QToolButton = QToolButton()
        self.loop_btn.setText("Loop")
        self.loop_btn.setCheckable(True)
        self.loop_btn.setChecked(True)
        self.loop_btn.toggled.connect(self.loopToggled)

        self.add_kf_btn: QToolButton = QToolButton()
        self.add_kf_btn.setText("＋◆")
        self.add_kf_btn.setToolTip("Add keyframe (A)")
        self.add_kf_btn.clicked.connect(
            lambda: self.addKeyframeClicked.emit(self._current)
        )

        self.del_kf_btn: QToolButton = QToolButton()
        self.del_kf_btn.setText("－◆")
        self.del_kf_btn.setToolTip("Delete keyframe (D)")
        self.del_kf_btn.clicked.connect(
            lambda: self.deleteKeyframeClicked.emit(self._current)
        )

        for btn in [
            self.play_btn,
            self.stop_btn,
            self.prev_kf_btn,
            self.next_kf_btn,
            self.loop_btn,
            self.add_kf_btn,
            self.del_kf_btn,
        ]:
            bar.addWidget(btn)

        bar.addSpacerItem(
            QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        self.time_label: QLabel = QLabel("00:00")
        self.time_label.setToolTip("Time (mm:ss)")
        self.frame_spin: QSpinBox = QSpinBox()
        self.frame_spin.setRange(0, 999999)
        self.frame_spin.setFixedWidth(70)
        self.frame_spin.valueChanged.connect(self.set_current_frame)
        self.fps_label: QLabel = QLabel("FPS:")
        self.fps_spin: QSpinBox = QSpinBox()
        self.fps_spin.setRange(1, 240)
        self.fps_spin.setValue(24)
        self.fps_spin.valueChanged.connect(self.fpsChanged.emit)

        self.in_label: QLabel = QLabel("In:")
        self.out_label: QLabel = QLabel("Out:")
        self.start_spin: QSpinBox = QSpinBox()
        self.end_spin: QSpinBox = QSpinBox()
        self.start_spin.setRange(0, 999999)
        self.end_spin.setRange(0, 999999)
        for w in [
            self.time_label,
            self.frame_spin,
            self.fps_label,
            self.fps_spin,
            self.in_label,
            self.start_spin,
            self.out_label,
            self.end_spin,
        ]:
            bar.addWidget(w)
        self.slider: QSlider = QSlider(Qt.Horizontal)
        self.slider.setVisible(False)
        self.fps_spinbox: QSpinBox = self.fps_spin
        self.start_frame_spinbox: QSpinBox = self.start_spin
        self.end_frame_spinbox: QSpinBox = self.end_spin
        self.frame_spinbox: QSpinBox = self.frame_spin
        self.start_spin.valueChanged.connect(self._on_range_spin)
        self.end_spin.valueChanged.connect(self._on_range_spin)
        self.slider.valueChanged.connect(self.set_current_frame)
        self.setFixedHeight(RULER_H + TRACK_H + TOOLBAR_H)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

    # --- Copy/Paste emit helpers (avoid fragile lambdas) ---
    def _emit_copy_at(self, idx: int) -> None:
        try:
            self.copyKeyframeClicked.emit(int(idx))
        except Exception:
            self.copyKeyframeClicked.emit(0)

    def _emit_paste_at(self, idx: int) -> None:
        try:
            self.pasteKeyframeClicked.emit(int(idx))
        except Exception:
            self.pasteKeyframeClicked.emit(0)

    def resizeEvent(self, e: QEvent) -> None:
        """
        Handles the resize event of the widget.

        Args:
            e: The resize event.
        """
        super().resizeEvent(e)
        self.toolbar.setGeometry(0, self.height() - TOOLBAR_H, self.width(), TOOLBAR_H)

    def set_current_frame(self, frame_index: int) -> None:
        """
        Sets the current frame of the timeline.

        Args:
            frame_index: The index of the frame to set.
        """
        frame_index = max(self._start, min(self._end, int(frame_index)))
        if self._current == frame_index:
            self._sync_frame_widgets()
            return
        self._current = frame_index
        self._sync_frame_widgets()
        self.frameChanged.emit(frame_index)
        self.update()

    def add_keyframe_marker(self, frame_index: int) -> None:
        """
        Adds a keyframe marker at the given frame index.

        Args:
            frame_index: The index of the frame to add the marker at.
        """
        self._kfs.add(int(frame_index))
        self._update_delete_button()
        self.update()

    def remove_keyframe_marker(self, frame_index: int) -> None:
        """
        Removes a keyframe marker from the given frame index.

        Args:
            frame_index: The index of the frame to remove the marker from.
        """
        self._kfs.discard(int(frame_index))
        self._update_delete_button()
        self.update()

    def clear_keyframes(self) -> None:
        """Removes all keyframe markers."""
        self._kfs.clear()
        self._update_delete_button()
        self.update()

    def _sync_frame_widgets(self) -> None:
        """Synchronizes the frame widgets with the current frame."""
        if self.frame_spin.value() != self._current:
            self.frame_spin.blockSignals(True)
            self.frame_spin.setValue(self._current)
            self.frame_spin.blockSignals(False)
        if self.slider.value() != self._current:
            self.slider.blockSignals(True)
            self.slider.setValue(self._current)
            self.slider.blockSignals(False)
        self._update_delete_button()
        self._update_time_label()

    def _update_delete_button(self) -> None:
        """Enables or disables the delete keyframe button based on whether the current frame has a keyframe."""
        self.del_kf_btn.setEnabled(self._current in self._kfs)

    def _on_range_spin(self) -> None:
        """Handles the value changed signal of the range spin boxes."""
        s: int = max(0, min(self.start_spin.value(), self.end_spin.value()))
        e: int = max(s, max(self.start_spin.value(), self.end_spin.value()))
        if (s, e) != (self._start, self._end):
            self._start, self._end = s, e
            self.slider.setRange(s, e)
            self._scroll_frames = max(0.0, self._scroll_frames)
            self.set_current_frame(min(max(self._current, s), e))
            self.rangeChanged.emit(s, e)
            self.update()

    def _on_play_clicked(self, checked: bool) -> None:
        """
        Handles the clicked signal of the play button.

        Args:
            checked: Whether the button is checked.
        """
        if checked:
            self.play_btn.setText("⏸")
            self.playClicked.emit()
        else:
            self.play_btn.setText("⏵")
            self.pauseClicked.emit()

    def _on_stop_clicked(self) -> None:
        """Handles the clicked signal of the stop button."""
        if self.play_btn.isChecked():
            self.play_btn.setChecked(False)
        self.stopClicked.emit()

    def _jump_prev_kf(self) -> None:
        """Jumps to the previous keyframe."""
        if not self._kfs:
            return
        sorted_kfs: List[int] = sorted(list(self._kfs), reverse=True)
        target: int = next((kf for kf in sorted_kfs if kf < self._current), -1)
        if target != -1:
            self.set_current_frame(target)
        else:  # wrap around
            self.set_current_frame(sorted_kfs[0])

    def _jump_next_kf(self) -> None:
        """Jumps to the next keyframe."""
        if not self._kfs:
            return
        sorted_kfs: List[int] = sorted(list(self._kfs))
        target: int = next((kf for kf in sorted_kfs if kf > self._current), -1)
        if target != -1:
            self.set_current_frame(target)
        else:  # wrap around
            self.set_current_frame(sorted_kfs[0])

    def _timeline_rect(self) -> QRect:
        """Returns the rectangle of the timeline area."""
        return QRect(0, RULER_H, self.width(), TRACK_H)

    def _ruler_rect(self) -> QRect:
        """Returns the rectangle of the ruler area."""
        return QRect(0, 0, self.width(), RULER_H)

    def _frame_to_x(self, frame: float) -> float:
        """Converts a frame number to a horizontal position."""
        return (frame - self._start - self._scroll_frames) * self._px_per_frame

    def _x_to_frame(self, x: float) -> int:
        """Converts a horizontal position to a frame number."""
        f = x / max(1e-6, self._px_per_frame) + self._start + self._scroll_frames
        return max(0, int(round(f)))

    def paintEvent(self, _: QEvent) -> None:
        """Handles the paint event of the widget."""
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing)
            # Colors from settings or defaults
            BG = _c("bg", "#1E1E1E")
            RULER_BG = _c("ruler_bg", "#2C2C2C")
            TRACK_BG = _c("track_bg", "#242424")
            TICK = _c("tick", "#8A8A8A")
            TICK_MAJOR = _c("tick_major", "#E0E0E0")
            PLAYHEAD = _c("playhead", "#65B0FF")
            KF_NORMAL = _c("kf", "#FFC107")
            KF_HOVER = _c("kf_hover", "#FFE082")
            INOUT_ALPHA = _alpha(30)

            p.fillRect(self.rect(), BG)
            ruler_rect = self._ruler_rect()
            timeline_rect = self._timeline_rect()
            p.fillRect(ruler_rect, RULER_BG)
            p.fillRect(timeline_rect, TRACK_BG)

            in_x, out_x = self._frame_to_x(self._start), self._frame_to_x(self._end)
            inout = QColor(0, 0, 0, INOUT_ALPHA)
            p.fillRect(
                QRectF(
                    timeline_rect.left(),
                    timeline_rect.top(),
                    in_x - timeline_rect.left(),
                    timeline_rect.height(),
                ),
                inout,
            )
            p.fillRect(
                QRectF(
                    out_x,
                    timeline_rect.top(),
                    timeline_rect.right() - out_x,
                    timeline_rect.height(),
                ),
                inout,
            )

            self._draw_ticks(p, ruler_rect, TICK, TICK_MAJOR)

            for fr in self._kfs:
                x = self._frame_to_x(fr)
                if x < 0 or x > self.width():
                    continue
                self._draw_kf(
                    p,
                    QPointF(x, timeline_rect.center().y()),
                    fr == self._hover_kf,
                    KF_NORMAL,
                    KF_HOVER,
                )

            px = self._frame_to_x(self._current)
            p.setPen(QPen(PLAYHEAD, PLAYHEAD_W))
            p.drawLine(int(px), 0, int(px), self.height() - TOOLBAR_H)

            if self.underMouse():
                pos = self.mapFromGlobal(self.cursor().pos())
                if self._ruler_rect().contains(pos) or self._timeline_rect().contains(
                    pos
                ):
                    fx = self._x_to_frame(pos.x())
                    hud = f"{fx} | {self._format_time(fx)}"
                    metrics = p.fontMetrics()
                    w = metrics.horizontalAdvance(hud) + 10
                    h = metrics.height() + 6
                    x = int(min(max(6, pos.x() - w // 2), self.width() - w - 6))
                    y = 6
                    p.setPen(Qt.NoPen)
                    p.setBrush(QColor(0, 0, 0, 160))
                    p.drawRoundedRect(QRectF(x, y, w, h), 6, 6)
                    p.setPen(QColor("#D0D0D0"))
                    p.drawText(x + 5, y + h - 5, hud)
        finally:
            try:
                p.end()
            except Exception:
                pass

    def _draw_ticks(
        self, p: QPainter, rr: QRect, tick: QColor, tick_major: QColor
    ) -> None:
        """
        Draws the ticks on the ruler.

        Args:
            p: The painter to use.
            rr: The rectangle of the ruler.
        """
        p.setPen(tick)
        target: int = 80
        step_frames: int = max(1, int(round(target / max(1.0, self._px_per_frame))))
        base: int = 1
        while base * 10 < step_frames:
            base *= 10
        for k in (1, 2, 5, 10):
            if base * k >= step_frames:
                step_frames = base * k
                break
        first: int = max(
            0,
            int(
                math.floor((self._start + self._scroll_frames) / step_frames)
                * step_frames
            ),
        )
        for f in range(first, self._end + 1, step_frames):
            x: float = self._frame_to_x(f)
            if x < rr.left() - 20 or x > rr.right() + 20:
                continue
            is_major: bool = f % (step_frames * 5) == 0
            p.setPen(tick_major if is_major else tick)
            h: float = rr.height() - 2 if is_major else rr.height() / 2
            p.drawLine(int(x), rr.bottom() - int(h), int(x), rr.bottom())
            if is_major:
                p.drawText(int(x) + 4, rr.top() + rr.height() - 6, f"{f}")

    def _draw_kf(
        self,
        p: QPainter,
        pos: QPointF,
        is_hovered: bool,
        kf_normal: QColor,
        kf_hover: QColor,
    ) -> None:
        """
        Draws a keyframe marker.

        Args:
            p: The painter to use.
            pos: The position to draw the marker at.
            is_hovered: Whether the marker is hovered.
        """
        color: QColor = kf_hover if is_hovered else kf_normal
        p.setPen(QPen(color.darker(150), 1))
        p.setBrush(QBrush(color))
        p.drawPolygon(
            QPolygonF(
                [
                    QPointF(pos.x(), pos.y() - DIAMOND_H / 2),
                    QPointF(pos.x() + DIAMOND_W / 2, pos.y()),
                    QPointF(pos.x(), pos.y() + DIAMOND_H / 2),
                    QPointF(pos.x() - DIAMOND_W / 2, pos.y()),
                ]
            )
        )

    def mousePressEvent(self, e: QMouseEvent) -> None:
        """
        Handles the mouse press event.

        Args:
            e: The mouse event.
        """
        pos: QPointF = e.position()
        if e.button() == Qt.LeftButton and (
            self._ruler_rect().contains(pos.toPoint())
            or self._timeline_rect().contains(pos.toPoint())
        ):
            self._dragging_playhead = True
            self.set_current_frame(self._x_to_frame(pos.x()))
        elif e.button() == Qt.RightButton:
            self._show_context_menu(e)
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        """
        Handles the mouse move event.

        Args:
            e: The mouse event.
        """
        if self._dragging_playhead:
            self.set_current_frame(self._x_to_frame(e.position().x()))
        else:
            self._hover_kf = self._kf_at_pos(e.position())
        self.update()

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        """
        Handles the mouse release event.

        Args:
            e: The mouse event.
        """
        if e.button() == Qt.LeftButton:
            self._dragging_playhead = False
        super().mouseReleaseEvent(e)

    def wheelEvent(self, e: QWheelEvent) -> None:
        """
        Handles the wheel event for zooming and scrolling.

        Args:
            e: The wheel event.
        """
        pos: QPointF = e.position()
        steps: float = e.angleDelta().y() / 120.0
        if e.modifiers() & Qt.ControlModifier:
            mouse_frame_before: int = self._x_to_frame(pos.x())
            self._px_per_frame = max(
                self._min_ppf,
                min(self._max_ppf, self._px_per_frame * (1.0 + steps * 0.1)),
            )
            mouse_frame_after: int = self._x_to_frame(pos.x())
            self._scroll_frames += mouse_frame_before - mouse_frame_after
        else:
            self._scroll_frames -= steps * 15
        self._scroll_frames = max(0.0, self._scroll_frames)
        self.update()

    def keyPressEvent(self, e: QKeyEvent) -> None:
        """
        Handles key press events for shortcuts.

        Args:
            e: The key event.
        """
        if e.key() == Qt.Key_Space:
            self.play_btn.click()
            e.accept()
            return
        elif e.key() == Qt.Key_A:
            self.addKeyframeClicked.emit(self._current)
            e.accept()
            return
        elif e.key() == Qt.Key_D and self._current in self._kfs:
            self.deleteKeyframeClicked.emit(self._current)
            e.accept()
            return
        elif e.key() == Qt.Key_Home:
            self.set_current_frame(self._start)
            e.accept()
            return
        elif e.key() == Qt.Key_End:
            self.set_current_frame(self._end)
            e.accept()
            return
        elif e.key() == Qt.Key_Left:
            self._jump_prev_kf()
            e.accept()
            return
        elif e.key() == Qt.Key_Right:
            self._jump_next_kf()
            e.accept()
            return
        elif e.key() == Qt.Key_C and (e.modifiers() & Qt.ControlModifier):
            if self._current in self._kfs:
                self.copyKeyframeClicked.emit(self._current)
                e.accept()
                return
        elif e.key() == Qt.Key_V and (e.modifiers() & Qt.ControlModifier):
            self.pasteKeyframeClicked.emit(self._current)
            e.accept()
            return
        else:
            super().keyPressEvent(e)

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        """
        Handles mouse double click events for adding keyframes.

        Args:
            e: The mouse event.
        """
        if e.button() == Qt.LeftButton and self._timeline_rect().contains(
            e.position().toPoint()
        ):
            self.addKeyframeClicked.emit(self._x_to_frame(e.position().x()))
        super().mouseDoubleClickEvent(e)

    def _kf_at_pos(self, pos: QPointF) -> Optional[int]:
        """
        Returns the keyframe at the given position, if any.

        Args:
            pos: The position to check.

        Returns:
            The keyframe at the given position, or None.
        """
        if not self._timeline_rect().contains(pos.toPoint()):
            return None
        f: int = self._x_to_frame(pos.x())
        tol_frames: int = max(1, round(DIAMOND_W / (2 * max(1.0, self._px_per_frame))))
        return next((fr for fr in self._kfs if abs(fr - f) <= tol_frames), None)

    def _show_context_menu(self, e: QMouseEvent) -> None:
        """
        Shows the context menu for the timeline.

        Args:
            e: The mouse event.
        """
        menu: QMenu = QMenu(self)
        f: int = self._x_to_frame(e.position().x())
        add_action: QAction = QAction(f"Add keyframe @ {f}", self)
        add_action.triggered.connect(lambda: self.addKeyframeClicked.emit(f))
        menu.addAction(add_action)
        kf_at_cursor: Optional[int] = self._kf_at_pos(e.position())
        if kf_at_cursor is not None:
            rem_action: QAction = QAction(f"Delete keyframe @ {kf_at_cursor}", self)
            rem_action.triggered.connect(
                lambda: self.deleteKeyframeClicked.emit(kf_at_cursor)
            )
            menu.addAction(rem_action)
            copy_action: QAction = QAction(f"Copy keyframe @ {kf_at_cursor}", self)
            from functools import partial as _partial
            copy_action.triggered.connect(_partial(self._emit_copy_at, int(kf_at_cursor)))
            menu.addAction(copy_action)
        paste_action: QAction = QAction(f"Paste @ {f}", self)
        from functools import partial as _partial
        paste_action.triggered.connect(_partial(self._emit_paste_at, int(f)))
        menu.addAction(paste_action)
        menu.exec(e.globalPosition().toPoint())

    def _format_time(self, frame: int) -> str:
        """
        Formats the given frame number as a time string (mm:ss).

        Args:
            frame: The frame number to format.

        Returns:
            The formatted time string.
        """
        if self._fps <= 0:
            return "00:00"
        secs: float = frame / float(self._fps)
        return f"{int(secs // 60):02d}:{int(secs % 60):02d}"

    def _update_time_label(self) -> None:
        """Updates the time label with the current time."""
        self.time_label.setText(self._format_time(self._current))
