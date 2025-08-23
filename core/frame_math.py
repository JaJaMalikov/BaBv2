"""Pure frame math utilities for playback and navigation.

This module centralizes common computations around frame ranges, clamping,
stepping, and looping. It is intentionally Qt-free and safe for use in tests
and core logic.
"""

from __future__ import annotations

from typing import Tuple


def clamp(value: int, lo: int, hi: int) -> int:
    """Clamp ``value`` into the inclusive range [lo, hi] assuming lo <= hi.

    If the range is invalid (lo > hi), returns ``value`` unchanged.
    """
    if lo > hi:
        return int(value)
    if value < lo:
        return int(lo)
    if value > hi:
        return int(hi)
    return int(value)


def compute_next_playback_frame(
    current: int, start: int, end: int, loop_enabled: bool
) -> Tuple[int, bool]:
    """Compute the next frame index for playback.

    Returns a tuple (next_index, should_stop):
    - next_index: the frame to move to if not stopping; if stopping, it's the
      current value.
    - should_stop: True when playback should pause/stop at the current frame
      because we reached beyond the end and looping is disabled.

    Behavior mirrors controllers.playback_service.PlaybackService.next_frame.
    """
    # Normalize an invalid range by swapping if needed
    if end < start:
        start, end = end, start
    new_frame = current + 1
    if new_frame > end:
        if loop_enabled:
            return start, False
        return current, True
    return new_frame, False
