from core.svg_loader import SvgLoader

PARENT_MAP = {
    "torse": None,
    "cou": "torse",
    "tete": "cou",
    "epaule_droite": "torse",
    "haut_bras_droite": "epaule_droite",
    "coude_droite": "haut_bras_droite",
    "avant_bras_droite": "coude_droite",
    "main_droite": "avant_bras_droite",
    "epaule_gauche": "torse",
    "haut_bras_gauche": "epaule_gauche",
    "coude_gauche": "haut_bras_gauche",
    "avant_bras_gauche": "coude_gauche",
    "main_gauche": "avant_bras_gauche",
    "hanche_droite": "torse",
    "cuisse_droite": "hanche_droite",
    "genou_droite": "cuisse_droite",
    "tibia_droite": "genou_droite",
    "pied_droite": "tibia_droite",
    "hanche_gauche": "torse",
    "cuisse_gauche": "hanche_gauche",
    "genou_gauche": "cuisse_gauche",
    "tibia_gauche": "genou_gauche",
    "pied_gauche": "tibia_gauche",
}

PIVOT_MAP = {
    "tete": "cou",
    "haut_bras_droite": "epaule_droite",
    "avant_bras_droite": "coude_droite",
    "haut_bras_gauche": "epaule_gauche",
    "avant_bras_gauche": "coude_gauche",
    "cuisse_droite": "hanche_droite",
    "tibia_droite": "genou_droite",
    "cuisse_gauche": "hanche_gauche",
    "tibia_gauche": "genou_gauche",
    "cou": "cou",
    "epaule_droite": "epaule_droite",
    "coude_droite": "coude_droite",
    "epaule_gauche": "epaule_gauche",
    "coude_gauche": "coude_gauche",
    "hanche_droite": "hanche_droite",
    "genou_droite": "genou_droite",
    "hanche_gauche": "hanche_gauche",
    "genou_gauche": "genou_gauche",
    "torse": "torse"
}

Z_ORDER = {
    "torse": 0,  
    "cou": -1,
    "tete": -1,
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


def compute_child_map(parent_map):
    child_map = {}
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
    def __init__(self, name, parent=None, pivot=(0, 0), bbox=(0, 0, 0, 0), z_order=0):
        self.name = name
        self.parent = parent
        self.children = []
        self.pivot = pivot
        self.bbox = bbox
        self.z_order = z_order

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def __repr__(self):
        return f"<{self.name} pivot={self.pivot} z={self.z_order}>"


class Puppet:
    def __init__(self):
        self.members = {}
        self.child_map = {}

    def build_from_svg(self, svg_loader, parent_map, pivot_map=None, z_order_map=None):
        self.child_map = compute_child_map(parent_map)
        groups = svg_loader.get_groups()
        for group_id in groups:
            if group_id not in parent_map:
                    continue
            bbox = svg_loader.get_group_bounding_box(group_id) or (0, 0, 0, 0)
            x_min, y_min, _, _ = bbox
            pivot_group = pivot_map[group_id] if pivot_map and group_id in pivot_map else group_id
            pivot_global = svg_loader.get_pivot(pivot_group)
            pivot = (pivot_global[0] - x_min, pivot_global[1] - y_min)
            z_order = z_order_map.get(group_id, 0) if z_order_map else 0
            self.members[group_id] = PuppetMember(group_id, None, pivot, bbox, z_order)
        for child, parent in parent_map.items():
            child_member = self.members.get(child)
            parent_member = self.members.get(parent) if parent else None
            if child_member and parent_member:
                parent_member.add_child(child_member)

    def get_root_members(self):
        return [m for m in self.members.values() if m.parent is None]

    def get_first_child_pivot(self, name):
        child_names = self.child_map.get(name, [])
        if child_names:
            target_member = self.members.get(child_names[0])
            if target_member:
                return target_member.pivot
        return None, None

    def get_handle_target_pivot(self, name):
        # Gère d'abord les exceptions, sinon prend le premier enfant
        if name in HANDLE_EXCEPTION:
            target_member = self.members.get(HANDLE_EXCEPTION[name])
            if target_member:
                return target_member.pivot
        return self.get_first_child_pivot(name)

    def print_hierarchy(self, member=None, indent=""):
        if member is None:
            for root in self.get_root_members():
                self.print_hierarchy(root, indent)
        else:
            print(f"{indent}- {member.name} (pivot={member.pivot} z={member.z_order})")
            for child in member.children:
                self.print_hierarchy(child, indent + "  ")


def validate_svg_structure(svg_loader, parent_map, pivot_map):
    groups_in_svg = set(svg_loader.get_groups())
    groups_in_map = set(parent_map.keys())
    pivots_in_map = set(pivot_map.values())
    missing_in_svg = groups_in_map - groups_in_svg
    extra_in_svg = groups_in_svg - groups_in_map
    pivots_missing = pivots_in_map - groups_in_svg

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


def main():
    svg_path = "assets/wesh.svg"
    loader = SvgLoader(svg_path)
    validate_svg_structure(loader, PARENT_MAP, PIVOT_MAP)
    puppet = Puppet()
    puppet.build_from_svg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)
    print("Hiérarchie des membres (z-order inclus) :")
    puppet.print_hierarchy()


if __name__ == "__main__":
    main()
