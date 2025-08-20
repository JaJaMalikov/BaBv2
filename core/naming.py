"""Naming utilities shared across layers.

This module provides helpers to generate unique names from a base label by
appending an incrementing numeric suffix. It is pure and independent of Qt,
so it can be used from core/, controllers/, and ui/ layers.

It also centralizes formatting of composite keys used to reference puppet
members in graphics maps (e.g. "<puppet>:<member>").
"""

from __future__ import annotations

from typing import Collection, Tuple

# Separator for composite keys used to address puppet members in UI visuals
MEMBER_KEY_SEP: str = ":"


def puppet_member_key(puppet_name: str, member_name: str) -> str:
    """Return the canonical composite key for a puppet member.

    Example: puppet_member_key("manu", "arm") -> "manu:arm"
    """
    return f"{puppet_name}{MEMBER_KEY_SEP}{member_name}"


def split_puppet_member_key(key: str) -> Tuple[str, str]:
    """Split a composite key into (puppet_name, member_name).

    This is lenient and splits on the first separator occurrence.
    Raises ValueError if the separator is not present.
    """
    if MEMBER_KEY_SEP not in key:
        raise ValueError("Invalid puppet member key: missing separator")
    puppet, member = key.split(MEMBER_KEY_SEP, 1)
    return puppet, member


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
