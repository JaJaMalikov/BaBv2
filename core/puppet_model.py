from typing import Dict, List, Optional, Tuple
from core.svg_loader import SvgLoader


PARENT_MAP: Dict[str, Optional[str]] = {
    "torse": None,
    "cou": "torse",
    "tete": "cou",
    "epaule_droite": "torse",
    "haut_bras_droite": "epaule_droite",
    "coude_droite": "haut_bras_droite",
    "avant_bras_droite": "coude_droite",
    "poignet_droite": "avant_bras_droite",
    "main_droite": "poignet_droite",
    "epaule_gauche": "torse",
    "haut_bras_gauche": "epaule_gauche",
    "coude_gauche": "haut_bras_gauche",
    "avant_bras_gauche": "coude_gauche",
    "poignet_gauche": "avant_bras_gauche",
    "main_gauche": "poignet_gauche",
    "hanche_droite": "torse",
    "cuisse_droite": "hanche_droite",
    "genou_droite": "cuisse_droite",
    "tibia_droite": "genou_droite",
    "cheville_droite": "tibia_droite",
    "pied_droite": "cheville_droite",
    "hanche_gauche": "torse",
    "cuisse_gauche": "hanche_gauche",
    "genou_gauche": "cuisse_gauche",
    "tibia_gauche": "cuisse_gauche",
    "cheville_gauche": "tibia_gauche",
    "pied_gauche": "cheville_gauche",
}

PIVOT_MAP: Dict[str, str] = {
    "tete": "cou",
    "haut_bras_droite": "epaule_droite",
    "avant_bras_droite": "coude_droite",
    "haut_bras_gauche": "epaule_gauche",
    "avant_bras_gauche": "coude_gauche",
    "cuisse_droite": "hanche_droite",
    "tibia_droite": "genou_droite",
    "cuisse_gauche": "hanche_gauche",
    "tibia_gauche": "genou_gauche",
    "main_droite": "poignet_droite",
    "main_gauche": "poignet_gauche",
    "pied_droite": "cheville_droite",
    "pied_gauche": "cheville_gauche"
}

Z_ORDER: Dict[str, int] = {
    "torse": 0,  
    "cou": -1,
    "tete": 1,
    "epaule_droite": 2,
    "haut_bras_droite": -1,
    "coude_droite": 2,
    "avant_bras_droite": 2,
    "main_droite": 3,
    "epaule_gauche": 2,
    "haut_bras_gauche": -1,
    "coude_gauche": 2,
    "avant_bras_gauche": 2,
    "main_gauche": 3,
    "hanche_droite": -1,
    "cuisse_droite": -2,
    "genou_droite": 2,
    "tibia_droite": 2,
    "pied_droite": 3,
    "hanche_gauche": -1,
    "cuisse_gauche": -2,
    "genou_gauche": 2,
    "tibia_gauche": 2,
    "pied_gauche": 3,
}


def compute_child_map(parent_map: Dict[str, Optional[str]]) -> Dict[str, List[str]]:
    child_map: Dict[str, List[str]] = {}
    for child, parent in parent_map.items():
        if parent:
            child_map.setdefault(parent, []).append(child)
    return child_map


CHILD_MAP = compute_child_map(PARENT_MAP)

# Mapping d'exception possible pour certains segments (ex : "torse" → "cou")
HANDLE_EXCEPTION = {
    # "torse": "cou",
    # Ajoute ici tes exceptions si besoin
}


class PuppetMember:
    def __init__(self, name: str, parent: Optional['PuppetMember'] = None, pivot: Tuple[float, float] = (0.0, 0.0), bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0), z_order: int = 0):
        self.name: str = name
        self.parent: Optional['PuppetMember'] = parent
        self.children: List['PuppetMember'] = []
        self.pivot: Tuple[float, float] = pivot
        self.bbox: Tuple[float, float, float, float] = bbox
        self.z_order: int = z_order
        self.rel_pos: Tuple[float, float] = (0.0, 0.0)

    def add_child(self, child: 'PuppetMember') -> None:
        self.children.append(child)
        child.parent = self
        child.rel_pos = (child.pivot[0] - self.pivot[0], child.pivot[1] - self.pivot[1])

    def __repr__(self) -> str:
        return f"<{self.name} pivot={self.pivot} z={self.z_order}>"


class Puppet:
    def __init__(self) -> None:
        self.members: Dict[str, PuppetMember] = {}
        self.child_map: Dict[str, List[str]] = {}

    def build_from_svg(self, svg_loader: 'SvgLoader', parent_map: Dict[str, Optional[str]], pivot_map: Optional[Dict[str, str]] = None, z_order_map: Optional[Dict[str, int]] = None) -> None:
        self.child_map = compute_child_map(parent_map)
        groups = svg_loader.get_groups()
        for group_id in groups:
            if group_id not in parent_map:
                    continue
            bbox = svg_loader.get_group_bounding_box(group_id) or (0.0, 0.0, 0.0, 0.0)
            pivot_group = pivot_map[group_id] if pivot_map and group_id in pivot_map else group_id
            pivot = svg_loader.get_pivot(pivot_group)
            z_order = z_order_map.get(group_id, 0) if z_order_map else 0
            self.members[group_id] = PuppetMember(group_id, None, pivot, bbox, z_order)
        for child, parent in parent_map.items():
            child_member = self.members.get(child)
            parent_member = self.members.get(parent) if parent else None
            if child_member and parent_member:
                parent_member.add_child(child_member)

    def get_root_members(self) -> List[PuppetMember]:
        return [m for m in self.members.values() if m.parent is None]

    def get_first_child_pivot(self, name: str) -> Tuple[float, float]:
        child_names = self.child_map.get(name, [])
        if child_names:
            target_member = self.members.get(child_names[0])
            if target_member:
                return target_member.pivot
        return (0.0, 0.0) # Return a default tuple of floats

    def get_handle_target_pivot(self, name: str) -> Tuple[float, float]:
        # Gère d\'abord les exceptions, sinon prend le premier enfant
        if name in HANDLE_EXCEPTION:
            target_member = self.members.get(HANDLE_EXCEPTION[name])
            if target_member:
                return target_member.pivot
        return self.get_first_child_pivot(name)

    def print_hierarchy(self, member: Optional[PuppetMember] = None, indent: str = "") -> None:
        if member is None:
            for root in self.get_root_members():
                self.print_hierarchy(root, indent)
        else:
            print(f"{indent}- {member.name} (pivot={member.pivot} z={member.z_order})")
            for child in member.children:
                self.print_hierarchy(child, indent + "  ")



def validate_svg_structure(svg_loader: 'SvgLoader', parent_map: Dict[str, Optional[str]], pivot_map: Dict[str, str]) -> None:
    groups_in_svg: set[str] = set(svg_loader.get_groups())
    groups_in_map: set[str] = set(parent_map.keys())
    pivots_in_map: set[str] = set(pivot_map.values())
    missing_in_svg: set[str] = groups_in_map - groups_in_svg
    extra_in_svg: set[str] = groups_in_svg - groups_in_map
    pivots_missing: set[str] = pivots_in_map - groups_in_svg

    print("\n--- Audit Structure SVG ---")
    if missing_in_svg:
        print("❌ Groupes définis dans parent_map absents du SVG :", missing_in_svg)
    else:
        print("✅ Tous les groupes du parent_map existent dans le SVG.")
    if extra_in_svg:
        print("⚠️ Groupes présents dans le SVG mais non utilisés dans parent_map :", extra_in_svg)
    if pivots_missing:
        print("❌ Pivots définis dans pivot_map absents du SVG :", pivots_missing)
    else:
        print("✅ Tous les pivots du pivot_map existent dans le SVG.")
    print("-----------------------------\n")


def main() -> None:
    svg_path: str = "assets/manululu.svg"
    loader: SvgLoader = SvgLoader(svg_path)
    validate_svg_structure(loader, PARENT_MAP, PIVOT_MAP)
    puppet: Puppet = Puppet()
    puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)
    print("Hiérarchie des membres (z-order inclus) :")
    puppet.print_hierarchy()


if __name__ == "__main__":
    main()
