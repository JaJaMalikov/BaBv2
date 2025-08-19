"""Naming utilities shared across layers.

This module provides helpers to generate unique names from a base label by
appending an incrementing numeric suffix. It is pure and independent of Qt,
so it can be used from core/, controllers/, and ui/ layers.
"""

from __future__ import annotations

from typing import Collection


def unique_name(base: str, existing: Collection[str], sep: str = "_") -> str:
    """Return a unique name based on ``base`` not present in ``existing``.

    Strategy:
    - If ``base`` is free, return it as-is.
    - Otherwise, append an incrementing suffix using ``sep``: base_1, base_2, ...

    Parameters
    ----------
    base:
        Preferred base name.
    existing:
        Collection of names already in use.
    sep:
        Separator between base and numeric suffix (default "_").
    """
    name = base
    if name not in existing:
        return name
    i = 1
    while True:
        candidate = f"{base}{sep}{i}"
        if candidate not in existing:
            return candidate
        i += 1
