"""DEPRECATED shim for PuppetPiece location change.

This module used to live in core/ but now resides in ui/scene/ to maintain
core purity (no PySide6 imports). Import PuppetPiece from
``ui.scene.puppet_piece`` instead.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - shim only used by static analyzers
    # Forward type for hints without importing Qt at runtime
    from ui.scene.puppet_piece import PuppetPiece as PuppetPiece  # noqa: F401


def __getattr__(name: str):  # pragma: no cover - runtime guard
    if name == "PuppetPiece":
        raise RuntimeError(
            "PuppetPiece moved to ui.scene.puppet_piece to keep core pure. "
            "Please import from ui.scene.puppet_piece."
        )
    raise AttributeError(name)
