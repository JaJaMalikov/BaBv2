"""Utilities to update piece and handle visibility consistently across the UI.

This centralizes logic duplicated in state application and puppet ops.
"""

from __future__ import annotations

from typing import Any

from core.puppet_piece import PuppetPiece


def update_piece_visibility(win: Any, piece: PuppetPiece, is_on: bool) -> None:
    """Set piece and its handles visibility, and sync handle state if visible."""
    try:
        piece.setVisible(is_on)
        piece.pivot_handle.setVisible(is_on)
        if piece.rotation_handle:
            piece.rotation_handle.setVisible(is_on)
        if is_on:
            try:
                handles_on = bool(getattr(win.view, "handles_btn").isChecked())
                piece.set_handle_visibility(handles_on)
            except Exception:  # keep resilient
                pass
            piece.update_handle_positions()
    except Exception:
        # Swallow UI runtime errors for robustness in tests
        pass
