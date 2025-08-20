"""Minimal stub for PuppetPiece used in tests.

This project historically provided :class:`PuppetPiece` in this module.
Only a very small surface is required for the tests so we keep a light
implementation here.
"""
from __future__ import annotations


class PuppetPiece:  # pragma: no cover - behaviour not under test
    """Lightweight stand‑in for the real graphics piece class."""

    def __init__(self, *args, **kwargs):
        self.local_rotation = 0.0
        self.parent_piece = None

    def setPos(self, *args, **kwargs):
        """Pretend to position the piece in the scene."""
        pass
