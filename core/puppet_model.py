"""Static puppet data structures and SVG-driven hierarchy building.

This module defines Puppet, PuppetMember and utility helpers used to build
the puppet hierarchy from an SVG file. The hierarchy, pivot and z-order data
are stored externally in ``puppet_config.json`` and loaded at runtime.
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
import json
import logging

from core.svg_loader import SvgLoader

logger = logging.getLogger(__name__)


def compute_child_map(
    parent_map: Dict[str, Optional[str]],
) -> defaultdict[str, List[str]]:
    """Compute reverse mapping: parent -> list of children."""
    child_map: defaultdict[str, List[str]] = defaultdict(list)
    for child, parent in parent_map.items():
        if parent:
            child_map[parent].append(child)
    return child_map


# Mapping d'exception possible pour certains segments (ex : "torse" → "cou")
HANDLE_EXCEPTION = {
    # "torse": "cou",
    # Ajoute ici tes exceptions si besoin
}


@dataclass
class PuppetMember:
    """Node in the puppet hierarchy with pivot, bbox and z-order metadata."""

    name: str
    parent: Optional["PuppetMember"] = None
    pivot: Tuple[float, float] = (0.0, 0.0)
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    z_order: int = 0
    rel_pos: Tuple[float, float] = (0.0, 0.0)
    children: List["PuppetMember"] = field(default_factory=list)

    def add_child(self, child: "PuppetMember") -> None:
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
        # Optional mapping of logical slots to variant member names
        # Example: {"main_gauche": ["main_gauche", "main_gauche_rev"]}
        self.variants: Dict[str, List[str]] = {}
        # Optional absolute z-order override per variant name
        self.variant_z: Dict[str, int] = {}

        if config_path:
            cfg_path = Path(config_path)
        else:
            cfg_path = Path(__file__).with_name("puppet_config.json")
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
        raw_variants = data.get("variants", {})
        self.variants, self.variant_z = normalize_variants(raw_variants)
        self.child_map = dict(compute_child_map(self.parent_map))

    def build_from_svg(self, svg_loader: "SvgLoader") -> None:
        """Build the in-memory Puppet from an SVG using the loaded configuration.

        This method inspects the SVG groups provided by SvgLoader and, for each
        group that is declared in the puppet configuration (parent_map/pivot_map/
        z_order_map), creates a corresponding PuppetMember with its pivot,
        bounding box and z-order. It also links parent/child relationships and
        materializes declared variant candidates when present.

        Parameters
        - svg_loader: SvgLoader
            Loader already initialized on the SVG asset. Must provide
            get_groups(), get_group_bounding_box(), and get_pivot().

        Notes
        - Members not present in parent_map are ignored (treated as non-puppet
          decorative groups).
        - Variants declared in the configuration are created when the variant
          group exists in the SVG, inheriting base slot parent and pivot.

        Example
        >>> from core.svg_loader import SvgLoader
        >>> from core.puppet_model import Puppet
        >>> loader = SvgLoader("assets/pantins/manu.svg")
        >>> puppet = Puppet()
        >>> puppet.build_from_svg(loader)
        >>> sorted(name for name in puppet.members)  # doctest: +ELLIPSIS
        [...]
        """
        # Validate structure before building (docs/tasks.md Task 6.36)
        validate_svg_structure(svg_loader, self.parent_map, self.pivot_map)
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

        # Intégrer les variantes éventuelles: créer des membres pour chaque
        # variante absente des maps, en héritant du parent/pivot/z du slot de base.
        if self.variants:
            for slot, cand_list in self.variants.items():
                if not isinstance(cand_list, list) or not cand_list:
                    continue
                base = slot
                base_parent_name = self.parent_map.get(base)
                base_pivot_group = self.pivot_map.get(base, base)
                base_z = self.z_order_map.get(base, 0)
                for cand in cand_list:
                    if cand in self.members:
                        continue
                    if cand not in groups:
                        continue
                    bbox = svg_loader.get_group_bounding_box(cand) or (
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                    )
                    pivot = svg_loader.get_pivot(base_pivot_group)
                    self.members[cand] = PuppetMember(
                        cand, None, pivot, bbox, int(base_z)
                    )
                    # Lier au même parent que la base si possible
                    if base_parent_name:
                        parent_member = self.members.get(base_parent_name)
                        if parent_member:
                            parent_member.add_child(self.members[cand])

    def get_root_members(self) -> List[PuppetMember]:
        """Return members with no parent (roots)."""
        return [m for m in self.members.values() if m.parent is None]

    def _resolve_child_pivot(
        self, name: str, override: Optional[str] = None
    ) -> Tuple[float, float]:
        """Return pivot of ``override`` member or the first child of ``name``."""
        target_name: Optional[str] = override
        if not target_name:
            child_names = self.child_map.get(name, [])
            if child_names:
                target_name = child_names[0]
        if target_name:
            target_member = self.members.get(target_name)
            if target_member:
                return target_member.pivot
        return (0.0, 0.0)

    def get_first_child_pivot(self, name: str) -> Tuple[float, float]:
        """Return pivot of the first child of a member, or (0,0) if none."""
        return self._resolve_child_pivot(name)

    def get_handle_target_pivot(self, name: str) -> Tuple[float, float]:
        """Pivot used for handle placement (exceptions or first child)."""
        override = HANDLE_EXCEPTION.get(name)
        return self._resolve_child_pivot(name, override)


def normalize_variants(
    raw_variants: object,
) -> tuple[Dict[str, List[str]], Dict[str, int]]:
    """Normalize the "variants" section from puppet_config into typed maps.

    Input formats supported per slot (flexible, order preserved when possible):
    - "name" (str): simplest form, no z override
    - {"name": str, "z": int} or {"name": str, "z_order": int}: with z override
    - [name, z] or (name, z): positional pair

    Any unknown/invalid shapes are ignored for robustness.

    Returns
    - tuple[Dict[str, List[str]], Dict[str, int]]
      First item is a mapping of slot -> list of variant member names.
      Second item maps individual variant names -> absolute z-order overrides.

    Example
    >>> raw = {
    ...   "hand_left": [
    ...       "hand_left",
    ...       {"name": "hand_left_rev", "z": 120},
    ...       ["hand_left_glove", 110],
    ...   ]
    ... }
    >>> names, zmap = normalize_variants(raw)
    >>> names["hand_left"]
    ['hand_left', 'hand_left_rev', 'hand_left_glove']
    >>> zmap["hand_left_rev"], zmap["hand_left_glove"]
    (120, 110)
    """
    vmap: Dict[str, List[str]] = {}
    vz: Dict[str, int] = {}
    if isinstance(raw_variants, dict):
        for slot, items in raw_variants.items():
            names: List[str] = []
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict):
                        nm = it.get("name")
                        if isinstance(nm, str):
                            names.append(nm)
                            zval = it.get("z")
                            if isinstance(zval, int):
                                vz[nm] = zval
                            else:
                                zval2 = it.get("z_order")
                                if isinstance(zval2, int):
                                    vz[nm] = zval2
                    elif isinstance(it, (list, tuple)) and len(it) == 2:
                        nm, zval = it[0], it[1]
                        if isinstance(nm, str):
                            names.append(nm)
                            if isinstance(zval, int):
                                vz[nm] = zval
                    elif isinstance(it, str):
                        names.append(it)
            vmap[str(slot)] = names
        return vmap, vz
    # Legacy: dict[str, list[str]] or invalid
    try:
        return dict(raw_variants), {}
    except Exception:  # pylint: disable=broad-except
        return {}, {}


def print_hierarchy(
    self, member: Optional[PuppetMember] = None, indent: str = ""
) -> None:
    """Print the puppet hierarchy starting from ``member`` (or roots)."""
    if member is None:
        for root in self.get_root_members():
            self.print_hierarchy(root, indent)
    else:
        logger.info(
            "%s- %s (pivot=%s z=%s)",
            indent,
            member.name,
            member.pivot,
            member.z_order,
        )
        for child in member.children:
            self.print_hierarchy(child, indent + "  ")


def validate_svg_structure(
    svg_loader: "SvgLoader",
    parent_map: Dict[str, Optional[str]],
    pivot_map: Dict[str, str],
) -> None:
    """Validate puppet parent/child relations and pivot references.

    This performs both an audit (logs) and strict validations with actionable
    error messages to help asset authors fix issues early.

    Validations performed (docs/tasks.md Task 6.36):
    - Every child in parent_map must exist in the SVG.
    - Referenced parents must exist in the SVG.
    - No member can be its own parent.
    - No cycles in the parent chain (walking parents must terminate at a root).
    - All pivot targets referenced in pivot_map must exist in the SVG.

    Parameters are identical to the previous audit helper; behavior is now
    stricter and raises ValueError on severe inconsistencies.
    """
    groups_in_svg: set[str] = set(svg_loader.get_groups())
    groups_in_map: set[str] = set(parent_map.keys())
    pivots_in_map: set[str] = set(pivot_map.values())

    missing_children: set[str] = groups_in_map - groups_in_svg
    parents_referenced: set[str] = {p for p in parent_map.values() if p}
    missing_parents: set[str] = parents_referenced - groups_in_svg
    pivots_missing: set[str] = pivots_in_map - groups_in_svg

    issues: list[str] = []

    # Log audit info
    logger.info("\n--- Audit Structure SVG ---")
    if missing_children:
        logger.warning(
            "❌ Groupes définis dans parent_map absents du SVG : %s", missing_children
        )
        issues.append(
            "Missing puppet members in SVG: " + ", ".join(sorted(missing_children))
        )
    else:
        logger.info("✅ Tous les groupes du parent_map existent dans le SVG.")

    extra_in_svg: set[str] = groups_in_svg - groups_in_map
    if extra_in_svg:
        logger.warning(
            "⚠️ Groupes présents dans le SVG mais non utilisés dans parent_map : %s",
            extra_in_svg,
        )

    if missing_parents:
        logger.warning(
            "❌ Parents référencés absents du SVG : %s", missing_parents
        )
        issues.append(
            "Missing referenced parents in SVG: " + ", ".join(sorted(missing_parents))
        )

    if pivots_missing:
        logger.warning(
            "❌ Pivots définis dans pivot_map absents du SVG : %s", pivots_missing
        )
        issues.append(
            "Missing pivot target groups in SVG: " + ", ".join(sorted(pivots_missing))
        )
    else:
        logger.info("✅ Tous les pivots du pivot_map existent dans le SVG.")

    # Self-parenting and cycles
    for child, parent in parent_map.items():
        if parent and parent == child:
            issues.append(f"Member '{child}' cannot be its own parent.")

    # Cycle detection by walking parent chain
    def _detect_cycle(start: str) -> Optional[list[str]]:
        seen: set[str] = set()
        order: list[str] = [start]
        cur = start
        while True:
            p = parent_map.get(cur)
            if not p:
                return None
            if p in seen:
                order.append(p)
                return order
            seen.add(p)
            order.append(p)
            cur = p

    for node in groups_in_map:
        cycle = _detect_cycle(node)
        if cycle:
            issues.append(
                "Cycle detected in parent chain: " + " -> ".join(cycle)
            )
            break

    logger.info("-----------------------------\n")

    if issues:
        # Combine issues into an actionable message
        raise ValueError(
            "Invalid puppet configuration / SVG structure:\n- "
            + "\n- ".join(issues)
        )


def main() -> None:
    """Run a quick validation and print the puppet hierarchy for debugging."""
    svg_path: str = "assets/manu.svg"
    loader: SvgLoader = SvgLoader(svg_path)
    puppet: Puppet = Puppet()
    validate_svg_structure(loader, puppet.parent_map, puppet.pivot_map)
    puppet.build_from_svg(loader)
    logger.info("Hiérarchie des membres (z-order inclus) :")
    puppet.print_hierarchy()


if __name__ == "__main__":
    main()
