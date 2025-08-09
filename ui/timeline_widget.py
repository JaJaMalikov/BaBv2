from __future__ import annotations

import math
from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent, QWheelEvent, QKeyEvent, QAction, QPolygonF
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, QSpinBox, QLabel,
    QStyleOptionSlider, QStyle, QMenu, QToolButton
)

# -------------------------
# Helpers
# -------------------------
@dataclass(frozen=True)
class KF:
    track: str
    frame: int

RULER_H = 24
TRACK_H = 20
TRACK_MARGIN = 4
PLAYHEAD_W = 2

BG = QColor("#121212")
RULER_BG = QColor("#1E1E1E")
TICK = QColor("#5C5C5C")
TICK_MAJOR = QColor("#A0A0A0")
PLAYHEAD = QColor("#65B0FF")
KF_NORMAL = QColor("#FFC107")
KF_HOVER = QColor("#FFE082")
KF_SELECT = QColor("#FFD65C")
INOUT_SHADE = QColor("#2A2A2A")

DIAMOND_W = 10
DIAMOND_H = 10

class TimelineWidget(QWidget):
    frameChanged = Signal(int)
    addKeyframeClicked = Signal(int)
    deleteKeyframeClicked = Signal(int)
    playClicked = Signal()
    pauseClicked = Signal()
    fpsChanged = Signal(int)
    rangeChanged = Signal(int, int)

    # New
    selectionChanged = Signal(list)           # list[KF]
    keyframeMoved = Signal(str, int, int)     # track, old, new
    zoomChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)
        self._minimized = False

        self._tracks: list[str] = ["Global"]
        self._kfs: dict[str, set[int]] = {"Global": set()}
        # Render policy: single visible track by default
        self._single_track = True
        # Auto-height: fit to visible tracks
        self._auto_height = True
        self._selection: set[KF] = set()

        # Model values
        self._start = 0
        self._end = 100
        self._fps = 24
        self._current = 0

        # View state
        self._px_per_frame = 10.0   # zoom
        self._min_ppf = 2.0
        self._max_ppf = 40.0
        self._scroll_frames = 0.0   # pan offset in frames
        self._hover_kf: KF | None = None
        self._dragging_playhead = False
        self._dragging_kf: list[KF] | None = None
        self._drag_origin_frame = 0

        # --- Layout root ---
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(5, 5, 5, 5)
        self._main_layout.addStretch()

        # Bottom toolbar (separate widget)
        self.toolbar = QWidget(self)
        bar = QHBoxLayout(self.toolbar)
        bar.setContentsMargins(4, 2, 4, 2)
        bar.setSpacing(6)
        # Transport
        self.play_btn = QToolButton(); self.play_btn.setText("⏵"); self.play_btn.setCheckable(True); self.play_btn.clicked.connect(self._on_play_clicked); bar.addWidget(self.play_btn)
        self.stop_btn = QToolButton(); self.stop_btn.setText("■"); self.stop_btn.setToolTip("Stop et retour au début"); self.stop_btn.clicked.connect(self._on_stop_clicked); bar.addWidget(self.stop_btn)
        self.loop_btn = QToolButton(); self.loop_btn.setText("Loop"); self.loop_btn.setCheckable(True); self.loop_btn.setChecked(True); self.loop_btn.toggled.connect(self._on_loop_toggled); bar.addWidget(self.loop_btn)
        # Keyframes
        self.add_kf_btn = QToolButton(); self.add_kf_btn.setText("＋◆"); self.add_kf_btn.setToolTip("Ajouter keyframe"); self.add_kf_btn.clicked.connect(lambda: self._emit_add_kf(self._current)); bar.addWidget(self.add_kf_btn)
        self.del_kf_btn = QToolButton(); self.del_kf_btn.setText("－◆"); self.del_kf_btn.setToolTip("Supprimer keyframe"); self.del_kf_btn.clicked.connect(lambda: self._emit_del_kf(self._current)); bar.addWidget(self.del_kf_btn)
        bar.addStretch()
        # Time/frame and FPS
        self.time_label = QLabel("00:00"); self.time_label.setToolTip("Temps (mm:ss)"); bar.addWidget(self.time_label)
        self.frame_spin = QSpinBox(); self.frame_spin.setRange(0, 999999); self.frame_spin.setFixedWidth(80); self.frame_spin.valueChanged.connect(self.set_current_frame); bar.addWidget(self.frame_spin)
        bar.addWidget(QLabel("FPS:"))
        self.fps_spin = QSpinBox(); self.fps_spin.setRange(1, 240); self.fps_spin.setValue(24); self.fps_spin.valueChanged.connect(self._on_fps_changed); bar.addWidget(self.fps_spin)
        self._main_layout.addWidget(self.toolbar)

        # Hidden slider kept for backward-compat with existing code
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(self._start, self._end)
        self.slider.valueChanged.connect(self.set_current_frame)
        self.slider.setVisible(False)
        self._main_layout.addWidget(self.slider)

        # Hidden Start/End/FPS spinboxes for API compatibility (not added to layout)
        self.start_spin = QSpinBox(); self.start_spin.setRange(0, 999999)
        self.start_spin.valueChanged.connect(self._on_range_spin)
        self.end_spin = QSpinBox(); self.end_spin.setRange(0, 999999); self.end_spin.setValue(100)
        self.end_spin.valueChanged.connect(self._on_range_spin)
        self.fps_spin = QSpinBox(); self.fps_spin.setRange(1, 240); self.fps_spin.setValue(24)
        self.fps_spin.valueChanged.connect(self._on_fps_changed)

        # Back-compat attribute aliases for v1 API
        self.fps_spinbox = self.fps_spin
        self.start_frame_spinbox = self.start_spin
        self.end_frame_spinbox = self.end_spin
        self.frame_spinbox = self.frame_spin

        # Toolbar overlay: no compact toggle needed
        self.set_compact(False)

        self.setFocusPolicy(Qt.StrongFocus)
        # HUD: show frame/time under cursor
        self.setMouseTracking(True)
        self._mouse_pos: QPointF | None = None

        # lock height to visible tracks if auto_height
        self._apply_auto_height()

    def resizeEvent(self, e):
        super().resizeEvent(e)

    # -------------------------
    # Public API
    # -------------------------
    def set_total_frames(self, num_frames: int):
        self._end = int(num_frames)
        self.end_spin.setValue(self._end)
        self.slider.setRange(self._start, self._end)
        self.update()

    def set_current_frame(self, frame_index: int):
        frame_index = max(self._start, min(self._end, int(frame_index)))
        if self._current == frame_index:
            # keep UI in sync but avoid loops
            self._sync_frame_widgets()
            return
        self._current = frame_index
        self._sync_frame_widgets()
        self.frameChanged.emit(frame_index)
        self._update_time_label()
        self.update()

    def add_keyframe_marker(self, frame_index: int, track: str = "Global"):
        self.ensure_track(track)
        self._kfs[track].add(int(frame_index))
        self._update_delete_button()
        self.update()

    def remove_keyframe_marker(self, frame_index: int, track: str = "Global"):
        if track in self._kfs:
            self._kfs[track].discard(int(frame_index))
        self._update_delete_button()
        self.update()

    def clear_keyframes(self, track: str | None = None):
        if track is None:
            for t in self._kfs:
                self._kfs[t].clear()
        else:
            self.ensure_track(track)
            self._kfs[track].clear()
        self._selection.clear()
        self._update_delete_button()
        self.update()

    def set_tracks(self, names: list[str]):
        self._tracks = names[:] if names else ["Global"]
        for n in self._tracks:
            self._kfs.setdefault(n, set())
        self.update()

    def ensure_track(self, name: str):
        if name not in self._tracks:
            self._tracks.append(name)
        self._kfs.setdefault(name, set())

    def _visible_tracks(self) -> list[str]:
        return ["Global"] if getattr(self, "_single_track", False) else self._tracks

    def set_single_track(self, enabled: bool = True):
        """If enabled, only the 'Global' track is displayed (others stay in data)."""
        self._single_track = bool(enabled)
        self._apply_auto_height()
        self.update()

    def set_auto_height(self, enabled: bool = True):
        """Fit widget height to the number of visible tracks (clean look)."""
        self._auto_height = bool(enabled)
        self._apply_auto_height()
        self.update()

    def _apply_auto_height(self):
        # Ruler + tracks + bottom toolbar
        toolbar_h = self.toolbar.sizeHint().height() if hasattr(self, 'toolbar') and self.toolbar is not None else 0
        rows = max(1, len(self._visible_tracks()))
        total = 6 + RULER_H + rows * (TRACK_H + TRACK_MARGIN) + 6 + toolbar_h
        self.setMinimumHeight(total)
        self.setMaximumHeight(16777215)

    # No minimize API: visibility is handled by the dock itself

    # -------------------------
    # Internals — UI sync
    # -------------------------
    def set_compact(self, compact: bool = True):
        """Compact mode hides the heavy toolbar for a clean, minimal look."""
        self._compact = bool(compact)
        # Hide the whole toolbar widget to reclaim layout space
        if hasattr(self, 'toolbar') and self.toolbar is not None:
            self.toolbar.setVisible(not self._compact)
        # tighten top margins a bit when compact
        lay = self.layout()
        if isinstance(lay, QVBoxLayout):
            lay.setContentsMargins(5, 2 if self._compact else 5, 5, 5)
        self.update()

    # -------------------------
    def _sync_frame_widgets(self):
        if self.frame_spin.value() != self._current:
            self.frame_spin.setValue(self._current)
        if self.slider.value() != self._current:
            self.slider.setValue(self._current)
        self.del_kf_btn.setEnabled(any(self._current in self._kfs[t] for t in self._visible_tracks()))

    def _update_delete_button(self):
        self.del_kf_btn.setEnabled(any(self._current in self._kfs[t] for t in self._visible_tracks()))

    def _on_range_spin(self):
        s = max(0, min(self.start_spin.value(), self.end_spin.value()))
        e = max(s, max(self.start_spin.value(), self.end_spin.value()))
        if (s, e) != (self._start, self._end):
            self._start, self._end = s, e
            self.slider.setRange(s, e)
            # clamp current frame and pan
            self._scroll_frames = max(0.0, self._scroll_frames)
            self.set_current_frame(min(max(self._current, s), e))
            self.rangeChanged.emit(s, e)
            self.update()

    def _on_fps_changed(self, v: int):
        self._fps = v
        self.fpsChanged.emit(v)
        self._update_time_label()

    def _on_play_clicked(self, checked: bool):
        if checked:
            self.play_btn.setText("⏸")
            self.playClicked.emit()
        else:
            self.play_btn.setText("⏵")
            self.pauseClicked.emit()

    def _ppf_to_slider(self, ppf: float) -> int:
        # Map ppf [min,max] to [0,100]
        t = (ppf - self._min_ppf) / (self._max_ppf - self._min_ppf)
        return int(max(0, min(1, t)) * 100)

    def _slider_to_ppf(self, v: int) -> float:
        t = v / 100.0
        return self._min_ppf + t * (self._max_ppf - self._min_ppf)

    # Mouse-driven zoom only; no UI slider

    def _emit_add_kf(self, frame: int):
        self.addKeyframeClicked.emit(int(frame))

    def _emit_del_kf(self, frame: int):
        self.deleteKeyframeClicked.emit(int(frame))

    # -------------------------
    # Geometry helpers
    # -------------------------
    def _timeline_rect(self) -> QRect:
        return QRect(5, RULER_H + 1, self.width() - 10, max(1, self.height() - RULER_H - 6))

    def _ruler_rect(self) -> QRect:
        return QRect(5, 5, self.width() - 10, RULER_H - 10)

    def _track_y(self, idx: int) -> int:
        return RULER_H + 2 + idx * (TRACK_H + TRACK_MARGIN)

    def _frame_to_x(self, frame: float) -> float:
        return 10 + (frame - self._start - self._scroll_frames) * self._px_per_frame

    def _x_to_frame(self, x: float) -> int:
        f = (x - 10) / max(1e-6, self._px_per_frame) + self._start + self._scroll_frames
        return max(0, int(round(f)))

    # -------------------------
    # Painting
    # -------------------------
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), BG)

        # Ruler
        rr = self._ruler_rect()
        p.fillRect(rr, RULER_BG)

        # IN/OUT shading
        tl = self._timeline_rect()
        in_x = self._frame_to_x(self._start)
        out_x = self._frame_to_x(self._end)
        if in_x > tl.left():
            p.fillRect(QRectF(tl.left(), tl.top(), in_x - tl.left(), tl.height()), INOUT_SHADE)
        if out_x < tl.right():
            p.fillRect(QRectF(out_x, tl.top(), tl.right() - out_x, tl.height()), INOUT_SHADE)

        # Ticks
        self._draw_ticks(p, rr)

        # Tracks background grid
        for i, _t in enumerate(self._visible_tracks()):
            y = self._track_y(i)
            p.fillRect(QRectF(5, y, self.width() - 10, TRACK_H), QColor(255,255,255,10) if i % 2 == 0 else QColor(255,255,255,4))

        # Keyframes
        for i, tname in enumerate(self._visible_tracks()):
            for fr in self._kfs.get(tname, ()):  # draw only visible ones
                x = self._frame_to_x(fr)
                if x < 5 or x > self.width() - 5:
                    continue
                self._draw_kf(p, QPointF(x, self._track_y(i) + TRACK_H/2), KF(tname, fr))

        # Playhead
        px = self._frame_to_x(self._current)
        pen = QPen(PLAYHEAD, PLAYHEAD_W)
        p.setPen(pen)
        p.drawLine(int(px), RULER_H, int(px), self.height()-2)

        # HUD (mouse frame/time)
        if self._mouse_pos is not None:
            fx = self._x_to_frame(self._mouse_pos.x())
            hud = f"{fx}  |  {self._format_time(fx)}"
            metrics_rect = p.boundingRect(self.rect(), 0, hud)
            w = metrics_rect.width() + 10
            h = metrics_rect.height() + 6
            x = int(min(max(6, self._mouse_pos.x() + 12), self.width() - w - 6))
            y = 6
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 160))
            p.drawRoundedRect(QRectF(x, y, w, h), 6, 6)
            p.setPen(QColor('#D0D0D0'))
            p.drawText(x + 6, y + h - 6, hud)

        p.end()

    def _draw_ticks(self, p: QPainter, rr: QRect):
        p.setPen(TICK)
        p.setBrush(Qt.NoBrush)

        # dynamic spacing: aim ~80px between major ticks
        target = 80
        step_frames = max(1, int(round(target / max(1.0, self._px_per_frame))))
        # round step to 1/2/5 multiples
        base = 1
        while base < step_frames:
            for k in (1,2,5):
                if base * k >= step_frames:
                    step_frames = base * k
                    break
            base *= 10

        first = max(0, int(math.floor((self._start + self._scroll_frames) / step_frames) * step_frames))
        last = self._end
        for f in range(first, last + 1, step_frames):
            x = self._frame_to_x(f)
            if x < rr.left()-20 or x > rr.right()+20:
                continue
            is_major = (f % (step_frames*5) == 0)
            p.setPen(TICK_MAJOR if is_major else TICK)
            h = rr.height()-2 if is_major else rr.height()/2
            p.drawLine(int(x), rr.bottom()-int(h), int(x), rr.bottom())
            if is_major:
                p.drawText(int(x)+4, rr.top()+rr.height()-6, f"{f}")

    def _draw_kf(self, p: QPainter, pos: QPointF, kf: KF):
        sel = kf in self._selection
        hover = (self._hover_kf == kf)
        color = KF_SELECT if sel else (KF_HOVER if hover else KF_NORMAL)
        p.setPen(QPen(color.darker(150), 1))
        p.setBrush(QBrush(color))
        # diamond
        path = [
            QPointF(pos.x(), pos.y() - DIAMOND_H/2),
            QPointF(pos.x() + DIAMOND_W/2, pos.y()),
            QPointF(pos.x(), pos.y() + DIAMOND_H/2),
            QPointF(pos.x() - DIAMOND_W/2, pos.y()),
        ]
        poly = QPolygonF(path)
        p.drawPolygon(poly)

    # -------------------------
    # Mouse/keyboard
    # -------------------------
    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            f = self._x_to_frame(e.position().x())
            if e.position().y() <= RULER_H:
                self._dragging_playhead = True
                self.set_current_frame(f)
                self.update()
                return
            # tracks area
            kf = self._kf_at_pos(e.position())
            if kf:
                if e.modifiers() & Qt.ControlModifier:
                    # toggle selection
                    if kf in self._selection:
                        self._selection.remove(kf)
                    else:
                        self._selection.add(kf)
                    self.selectionChanged.emit(list(self._selection))
                else:
                    if kf not in self._selection:
                        self._selection = {kf}
                        self.selectionChanged.emit(list(self._selection))
                    # start drag
                    self._dragging_kf = list(self._selection)
                    self._drag_origin_frame = f
                self.update()
            else:
                # empty space: clear selection and set playhead
                if not (e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)):
                    if self._selection:
                        self._selection.clear()
                        self.selectionChanged.emit([])
                self.set_current_frame(f)
                self.update()
        elif e.button() == Qt.RightButton:
            self._show_context_menu(e)
        try:
            super().mousePressEvent(e)
        except Exception:
            pass

    def mouseMoveEvent(self, e: QMouseEvent):
        self._mouse_pos = e.position()
        f = self._x_to_frame(e.position().x())
        if self._dragging_playhead:
            self.set_current_frame(f)
        elif self._dragging_kf is not None:
            # preview move (snap)
            delta = f - self._drag_origin_frame
            # draw ghost by simply moving playhead; final move on release
            # (we visually keep selection; the real update is emitted on release)
            pass
        else:
            self._hover_kf = self._kf_at_pos(e.position())
            self.update()

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            if self._dragging_playhead:
                self._dragging_playhead = False
            elif self._dragging_kf is not None:
                f = self._x_to_frame(e.position().x())
                delta = f - self._drag_origin_frame
                if delta != 0:
                    moved = []
                    for kf in sorted(self._dragging_kf, key=lambda k: k.frame):
                        oldf = kf.frame
                        newf = max(self._start, min(self._end, oldf + delta))
                        # collision: shift until free
                        while newf in self._kfs[kf.track] and newf != oldf:
                            newf += 1 if delta > 0 else -1
                        if oldf in self._kfs[kf.track]:
                            self._kfs[kf.track].remove(oldf)
                        self._kfs[kf.track].add(newf)
                        moved.append((kf.track, oldf, newf))
                    for t, o, n in moved:
                        self.keyframeMoved.emit(t, o, n)
                    # update selection to new positions
                    self._selection = {KF(t, n) for t, _o, n in moved}
                    self.selectionChanged.emit(list(self._selection))
                self._dragging_kf = None
                self.update()
        try:
            super().mouseReleaseEvent(e)
        except Exception:
            pass

    def wheelEvent(self, e: QWheelEvent):
        self._mouse_pos = e.position()
        deg = e.angleDelta().y() / 8
        steps = deg / 15
        if e.modifiers() & Qt.ControlModifier:
            # zoom around mouse x
            self._px_per_frame = max(self._min_ppf, min(self._max_ppf, self._px_per_frame * (1.0 + steps*0.1)))
            # keep the frame under cursor stable
            mouse_frame = self._x_to_frame(e.position().x())
            x_after = self._frame_to_x(mouse_frame)
            dx = e.position().x() - x_after
            self._scroll_frames = max(0.0, self._scroll_frames - dx / max(1e-6, self._px_per_frame))
            self.update()
        else:
            # pan
            self._scroll_frames = max(0.0, self._scroll_frames - steps * 3)
            self.update()

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() == Qt.Key_Space:
            self.play_btn.toggle()
            self._on_play_clicked(self.play_btn.isChecked())
        elif e.key() == Qt.Key_Delete:
            if self._selection:
                for kf in list(self._selection):
                    if kf.frame in self._kfs.get(kf.track, set()):
                        self._kfs[kf.track].remove(kf.frame)
                        self.deleteKeyframeClicked.emit(kf.frame)
                self._selection.clear()
                self.selectionChanged.emit([])
                self.update()
        elif e.key() == Qt.Key_A:
            self._emit_add_kf(self._current)
        elif e.key() == Qt.Key_Home:
            self.set_current_frame(self._start)
        elif e.key() == Qt.Key_End:
            self.set_current_frame(self._end)
        elif e.modifiers() & Qt.ControlModifier and e.key() == Qt.Key_0:
            self._fit_range()
        elif e.key() == Qt.Key_I:
            # set IN to current
            if self._current <= self._end:
                self._start = max(0, min(self._current, self._end))
                self.start_spin.setValue(self._start)
                self.slider.setRange(self._start, self._end)
                self.update()
        elif e.key() == Qt.Key_O:
            # set OUT to current
            if self._current >= self._start:
                self._end = max(self._current, self._start)
                self.end_spin.setValue(self._end)
                self.slider.setRange(self._start, self._end)
                self.update()
        elif e.key() == Qt.Key_F:
            self._fit_range()

    # -------------------------
    # Hit‑testing & context menu
    # -------------------------
    def mouseDoubleClickEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton and e.position().y() > RULER_H:
            f = self._x_to_frame(e.position().x())
            idx = int((e.position().y() - (RULER_H + 2)) // (TRACK_H + TRACK_MARGIN))
            vis = self._visible_tracks()
            if 0 <= idx < len(vis):
                tname = vis[idx]
            else:
                tname = "Global"
            self._emit_add_kf(f)
        # don't swallow other default behaviors
        try:
            super().mouseDoubleClickEvent(e)
        except Exception:
            pass

    # -------------------------
    def _kf_at_pos(self, pos: QPointF) -> KF | None:
        # which track?
        if pos.y() <= RULER_H:
            return None
        idx = int((pos.y() - (RULER_H + 2)) // (TRACK_H + TRACK_MARGIN))
        vis = self._visible_tracks()
        if idx < 0 or idx >= len(vis):
            return None
        tname = vis[idx]
        f = self._x_to_frame(pos.x())
        # tolerance in pixels → frames
        tol_frames = max(0, round(DIAMOND_W / max(1.0, self._px_per_frame)))
        for fr in self._kfs.get(tname, set()):
            if abs(fr - f) <= tol_frames:
                return KF(tname, fr)
        return None

    def _show_context_menu(self, e: QMouseEvent):
        menu = QMenu(self)
        f = self._x_to_frame(e.position().x())
        kf = self._kf_at_pos(e.position())
        add = QAction("Add keyframe @ {}".format(f), self)
        add.triggered.connect(lambda: self._emit_add_kf(f))
        menu.addAction(add)
        if kf:
            rem = QAction("Delete keyframe", self)
            rem.triggered.connect(lambda: self._emit_del_kf(kf.frame))
            menu.addAction(rem)
        menu.exec(e.globalPosition().toPoint())

    # -------------------------
    # Utilities
    # -------------------------
    def _format_time(self, frame: int) -> str:
        if self._fps <= 0:
            return "00:00"
        secs = frame / float(self._fps)
        m = int(secs // 60)
        s = int(secs % 60)
        return f"{m:02d}:{s:02d}"

    def _on_stop_clicked(self):
        # Ensure play is off and emit stop
        if self.play_btn.isChecked():
            self.play_btn.setChecked(False)
            self.play_btn.setText("⏵")
        self.stopClicked.emit()

    def _on_loop_toggled(self, checked: bool):
        self.loop_enabled = bool(checked)
        self.loopToggled.emit(self.loop_enabled)

    def _jump_prev_kf(self):
        target = None
        cur = self._current
        for t in self._visible_tracks():
            for fr in sorted(self._kfs.get(t, set())):
                if fr < cur:
                    target = fr if target is None or fr > target else target
        if target is not None:
            self.set_current_frame(target)

    def _jump_next_kf(self):
        target = None
        cur = self._current
        for t in self._visible_tracks():
            for fr in sorted(self._kfs.get(t, set())):
                if fr > cur:
                    target = fr if target is None or fr < target else target
        if target is not None:
            self.set_current_frame(target)

    def _fit_range(self):
        # Zoom to show Start..End fully
        visible_px = max(100, self.width() - 20)
        span = max(1, self._end - self._start)
        self._px_per_frame = max(self._min_ppf, min(self._max_ppf, visible_px / span))
        self.zoom_slider.setValue(self._ppf_to_slider(self._px_per_frame))
        self._scroll_frames = 0
        self.update()

    def _set_in_value(self, f: int):
        s = max(0, min(f, self._end))
        if s != self._start:
            self._start = s
            self.start_spin.setValue(s)
            self.slider.setRange(self._start, self._end)
            self.rangeChanged.emit(self._start, self._end)
            self.update()

    def _set_out_value(self, f: int):
        e = max(self._start, f)
        if e != self._end:
            self._end = e
            self.end_spin.setValue(e)
            self.slider.setRange(self._start, self._end)
            self.rangeChanged.emit(self._start, self._end)
            self.update()

    def _set_in_current(self):
        self._set_in_value(self._current)

    def _set_out_current(self):
        self._set_out_value(self._current)

    def _update_time_label(self):
        self.time_label.setText(self._format_time(self._current))

    # options menu removed per new UX
