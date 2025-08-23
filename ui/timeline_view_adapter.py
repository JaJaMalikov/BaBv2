"""TimelineViewAdapter: Protocol-friendly wrapper for TimelineWidget.

This adapter exposes the minimal TimelineWidgetContract surface used by
controllers/tests and adds a few test-oriented accessors to avoid touching
protected members of the concrete widget in tests.

- Aligns with ui/contracts.TimelineWidgetContract and TimelineViewProtocol.
- Avoids direct model mutations; purely UI-interaction wrapper.
"""

from __future__ import annotations


from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent

from ui.views.timeline_widget import TimelineWidget
from ui.contracts import TimelineViewProtocol


class TimelineViewAdapter(TimelineViewProtocol):
    """Adapter around TimelineWidget implementing the contract methods.

    Additional helpers are provided for tests:
    - get_current_frame() -> int
    - has_keyframe(index: int) -> bool
    - prev_keyframe() / next_keyframe()
    - get_pixels_per_frame() -> float
    - wheel_zoom(delta: int, ctrl: bool = True)
    - resize(w: int, h: int)
    - widget property to access underlying widget if needed in runtime wiring.
    """

    def __init__(self) -> None:
        self._w = TimelineWidget()

    # --- Contract methods ---
    def clear_keyframes(self) -> None:
        self._w.clear_keyframes()

    def add_keyframe_marker(self, index: int) -> None:
        self._w.add_keyframe_marker(index)

    def set_current_frame(self, index: int) -> None:
        self._w.set_current_frame(index)

    # --- Test helpers / thin wrappers around public UI ---
    def get_current_frame(self) -> int:
        # TimelineWidget stores current frame internally as _current
        return getattr(self._w, "_current", 0)

    def has_keyframe(self, index: int) -> bool:
        kfs = getattr(self._w, "_kfs", set())
        return int(index) in kfs

    def prev_keyframe(self) -> None:
        # Prefer using the public button to simulate UI
        btn = getattr(self._w, "prev_kf_btn", None)
        if btn is not None:
            btn.click()
        else:
            # Fallback to private method if button absent
            jump_prev = getattr(self._w, "_jump_prev_kf", None)
            if callable(jump_prev):
                jump_prev()

    def next_keyframe(self) -> None:
        btn = getattr(self._w, "next_kf_btn", None)
        if btn is not None:
            btn.click()
        else:
            jump_next = getattr(self._w, "_jump_next_kf", None)
            if callable(jump_next):
                jump_next()

    def get_pixels_per_frame(self) -> float:
        return float(getattr(self._w, "_px_per_frame", 1.0))

    def wheel_zoom(self, delta: int, ctrl: bool = True) -> None:
        # Construct a wheel event similar to tests
        mods = Qt.ControlModifier if ctrl else Qt.NoModifier
        ev = QWheelEvent(
            QPointF(0, 0),
            QPointF(0, 0),
            QPoint(0, 0),
            QPoint(0, int(delta)),
            Qt.NoButton,
            mods,
            Qt.ScrollBegin,
            False,
        )
        self._w.wheelEvent(ev)

    def resize(self, w: int, h: int) -> None:
        self._w.resize(w, h)

    # Expose underlying widget for runtime wiring if needed
    @property
    def widget(self) -> TimelineWidget:
        return self._w
