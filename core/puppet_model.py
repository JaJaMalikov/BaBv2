"""Static puppet data structures and SVG-driven hierarchy building.

This module defines Puppet, PuppetMember and utility helpers used to build
the puppet hierarchy from an SVG file. The hierarchy, pivot and z-order data
are stored externally in ``puppet_config.json`` and loaded at runtime.
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import logging

from core.svg_loader import SvgLoader

logger = logging.getLogger(__name__)


def compute_child_map(parent_map: Dict[str, Optional[str]]) -> Dict[str, List[str]]:
    """Compute reverse mapping: parent -> list of children."""
    child_map: Dict[str, List[str]] = {}
    for child, parent in parent_map.items():
        if parent:
            child_map.setdefault(parent, []).append(child)
    return child_map

# Mapping d'exception possible pour certains segments (ex : "torse" → "cou")
HANDLE_EXCEPTION = {
    # "torse": "cou",
    # Ajoute ici tes exceptions si besoin
}


class PuppetMember:
    """Node in the puppet hierarchy with pivot, bbox and z-order metadata."""

    def __init__(
        self,
        name: str,
        parent: Optional['PuppetMember'] = None,
        pivot: Tuple[float, float] = (0.0, 0.0),
        bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
        z_order: int = 0,
    ) -> None:
        """Initialize hierarchy node with pivot, bounding box and z-order."""
        self.name: str = name
        self.parent: Optional['PuppetMember'] = parent
        self.children: List['PuppetMember'] = []
        self.pivot: Tuple[float, float] = pivot
        self.bbox: Tuple[float, float, float, float] = bbox
        self.z_order: int = z_order
        self.rel_pos: Tuple[float, float] = (0.0, 0.0)

    def add_child(self, child: 'PuppetMember') -> None:
        """Attach child and compute its relative offset from this node's pivot."""
        self.children.append(child)
        child.parent = self
        child.rel_pos = (child.pivot[0] - self.pivot[0], child.pivot[1] - self.pivot[1])

    def __repr__(self) -> str:
        """Return a debug representation of the member."""
        return f"<{self.name} pivot={self.pivot} z={self.z_order}>"


class Puppet:
    """In-memory puppet composed of PuppetMember nodes built from an SVG file."""

    def __init__(self, config_path: Optional[str | Path] = None) -> None:
        """Create an empty puppet and load configuration from JSON."""
        self.members: Dict[str, PuppetMember] = {}
        self.parent_map: Dict[str, Optional[str]] = {}
        self.pivot_map: Dict[str, str] = {}
        self.z_order_map: Dict[str, int] = {}
        self.child_map: Dict[str, List[str]] = {}

        cfg_path = Path(config_path) if config_path else Path(__file__).with_name("puppet_config.json")
        try:
            with cfg_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except FileNotFoundError:
            logger.error("Puppet config file not found: %s", cfg_path)
            data = {}
        except json.JSONDecodeError:
            logger.error("Invalid puppet config JSON: %s", cfg_path)
            data = {}

        self.parent_map = data.get("parent", {})
        self.pivot_map = data.get("pivot", {})
        self.z_order_map = data.get("z_order", {})
        self.child_map = compute_child_map(self.parent_map)

    def build_from_svg(self, svg_loader: 'SvgLoader') -> None:
        """Populate members from an SVG using the loaded configuration."""
        groups = svg_loader.get_groups()
        for group_id in groups:
            if group_id not in self.parent_map:
                continue
            bbox = svg_loader.get_group_bounding_box(group_id) or (0.0, 0.0, 0.0, 0.0)
            pivot_group = self.pivot_map.get(group_id, group_id)
            pivot = svg_loader.get_pivot(pivot_group)
            z_order = self.z_order_map.get(group_id, 0)
            self.members[group_id] = PuppetMember(group_id, None, pivot, bbox, z_order)

        for child, parent in self.parent_map.items():
            child_member = self.members.get(child)
            parent_member = self.members.get(parent) if parent else None
            if child_member and parent_member:
                parent_member.add_child(child_member)

    def get_root_members(self) -> List[PuppetMember]:
        """Return members with no parent (roots)."""
        return [m for m in self.members.values() if m.parent is None]

    def get_first_child_pivot(self, name: str) -> Tuple[float, float]:
        """Return pivot of the first child of a member, or (0,0) if none."""
        child_names = self.child_map.get(name, [])
        if child_names:
            target_member = self.members.get(child_names[0])
            if target_member:
                return target_member.pivot
        return (0.0, 0.0) # Return a default tuple of floats

    def get_handle_target_pivot(self, name: str) -> Tuple[float, float]:
        """Pivot used for handle placement (exceptions or first child)."""
        # Gère d'abord les exceptions, sinon prend le premier enfant
        if name in HANDLE_EXCEPTION:
            target_member = self.members.get(HANDLE_EXCEPTION[name])
            if target_member:
                return target_member.pivot
        return self.get_first_child_pivot(name)

    def print_hierarchy(self, member: Optional[PuppetMember] = None, indent: str = "") -> None:
        """Print the puppet hierarchy starting from ``member`` (or roots)."""
        if member is None:
            for root in self.get_root_members():
                self.print_hierarchy(root, indent)
        else:
            logger.info(f"{indent}- {member.name} (pivot={member.pivot} z={member.z_order})")
            for child in member.children:
                self.print_hierarchy(child, indent + "  ")



def validate_svg_structure(svg_loader: 'SvgLoader', parent_map: Dict[str, Optional[str]], pivot_map: Dict[str, str]) -> None:
    """Audit the SVG against parent/pivot maps and print discrepancies."""
    groups_in_svg: set[str] = set(svg_loader.get_groups())
    groups_in_map: set[str] = set(parent_map.keys())
    pivots_in_map: set[str] = set(pivot_map.values())
    missing_in_svg: set[str] = groups_in_map - groups_in_svg
    extra_in_svg: set[str] = groups_in_svg - groups_in_map
    pivots_missing: set[str] = pivots_in_map - groups_in_svg

    logger.info("\n--- Audit Structure SVG ---")
    if missing_in_svg:
        logger.warning("❌ Groupes définis dans parent_map absents du SVG : %s", missing_in_svg)
    else:
        logger.info("✅ Tous les groupes du parent_map existent dans le SVG.")
    if extra_in_svg:
        logger.warning("⚠️ Groupes présents dans le SVG mais non utilisés dans parent_map : %s", extra_in_svg)
    if pivots_missing:
        logger.warning("❌ Pivots définis dans pivot_map absents du SVG : %s", pivots_missing)
    else:
        logger.info("✅ Tous les pivots du pivot_map existent dans le SVG.")
    logger.info("-----------------------------\n")


def main() -> None:
    """Run a quick validation and print the puppet hierarchy for debugging."""
    svg_path: str = "assets/manululu.svg"
    loader: SvgLoader = SvgLoader(svg_path)
    puppet: Puppet = Puppet()
    validate_svg_structure(loader, puppet.parent_map, puppet.pivot_map)
    puppet.build_from_svg(loader)
    logger.info("Hiérarchie des membres (z-order inclus) :")
    puppet.print_hierarchy()


if __name__ == "__main__":
    main()
