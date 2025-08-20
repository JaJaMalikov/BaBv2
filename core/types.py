from __future__ import annotations

"""Typed aliases and structures for core scene state maps.

These types are used to document and check the structure of scene snapshots
(keyframes, object states, puppet member states) across core and controllers.
They aim to be minimally invasive and compatible with existing JSON format.
"""

from typing import TypedDict, Dict, Any, Optional, Tuple
from enum import Enum


class ObjectState(TypedDict, total=False):
    x: float
    y: float
    rotation: float
    scale: float
    z: int
    # Attachment expressed by names; None means free in scene
    attached_to: Optional[Tuple[str, str]]
    # Additional fields may exist (file_path, obj_type) when sourced from to_dict


# Puppet state is a mapping puppet member name -> arbitrary member state map.
# We keep member state values as Any for now while the Puppet API evolves.
PuppetMemberState = Dict[str, Any]
PuppetState = Dict[str, PuppetMemberState]

# Aggregated maps used inside keyframes
ObjectStateMap = Dict[str, ObjectState]
PuppetStateMap = Dict[str, PuppetState]


class SceneSnapshot(TypedDict, total=False):
    puppets: PuppetStateMap
    objects: ObjectStateMap


class Kind(Enum):
    """Enumerates high-level asset and item kinds used across the app.

    Using Enum prevents stringly-typed logic and centralizes allowed values.
    Values are lowercase to match persisted/serialized representations.
    """

    OBJECT = "object"
    PUPPET = "puppet"
    BACKGROUND = "background"

    @classmethod
    def from_str(cls, value: str | None) -> "Kind | None":
        if not value:
            return None
        val = value.lower().strip()
        for k in cls:
            if k.value == val:
                return k
        return None
