from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QRectF


class SvgLoader:
    def __init__(self, svg_path: str) -> None:
        self.svg_path = svg_path
        self.tree = ET.parse(svg_path)
        self.root = self.tree.getroot()
        self.namespaces = {"svg": "http://www.w3.org/2000/svg"}
        self.renderer = QSvgRenderer(svg_path)

    def get_group_offset(self, group_id: str) -> tuple[float, float] | None:
        """Return the top-left coordinates of ``group_id``."""

        rect: QRectF = self.renderer.boundsOnElement(group_id)
        if rect.isNull():
            return None

        return rect.left(), rect.top()

    def get_groups(self):
        groups = []
        for elem in self.root.findall(".//svg:g", self.namespaces):
            group_id = elem.attrib.get("id")
            if group_id:
                groups.append(group_id)
        return groups

    def get_group_bounding_box(self, group_id: str) -> tuple[float, float, float, float] | None:
        """Return the bounding box of ``group_id``.

        The coordinates are extracted using :class:`QSvgRenderer` to handle
        transforms correctly.
        """

        rect: QRectF = self.renderer.boundsOnElement(group_id)
        if rect.isNull():
            return None

        return (rect.left(), rect.top(), rect.right(), rect.bottom())

    def get_pivot(self, group_id):
        """
        Détermine le pivot (origine de rotation) du groupe
        en prenant le centre du plus petit cercle trouvé.
        """
        group_elem = self.root.find(
            f".//svg:g[@id='{group_id}']",
            self.namespaces
        )

        if group_elem is None:
            return 0, 0

        min_radius = None
        pivot_x = 0
        pivot_y = 0

        # First inspect <circle> elements directly
        for circ in group_elem.findall(".//svg:circle", self.namespaces):
            try:
                r = float(circ.attrib.get("r", "0"))
                cx = float(circ.attrib.get("cx", "0"))
                cy = float(circ.attrib.get("cy", "0"))
            except ValueError:
                continue

            if min_radius is None or r < min_radius:
                min_radius = r
                pivot_x = cx
                pivot_y = cy

        # Fallback to look for small path based circles
        for circle in group_elem.findall(".//svg:path", self.namespaces):
            d = circle.attrib.get("d")
            if d:
                bounds = self._get_path_bounds(d)
                if bounds:
                    x_min, y_min, x_max, y_max = bounds
                    width = x_max - x_min
                    height = y_max - y_min
                    radius = min(width, height) / 2
                    cx = x_min + width / 2
                    cy = y_min + height / 2

                    if min_radius is None or radius < min_radius:
                        min_radius = radius
                        pivot_x = cx
                        pivot_y = cy

        return pivot_x, pivot_y

    def _get_path_bounds(self, d):
        """
        Analyse grossièrement un chemin SVG pour trouver ses bornes min/max.
        """
        try:
            coords = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d)
            coords = [float(c) for c in coords]
            xs = coords[::2]
            ys = coords[1::2]
            if not xs or not ys:
                return None
            return min(xs), min(ys), max(xs), max(ys)
        except Exception as e:
            print(f"Erreur parsing path: {e}")
            return None

    def extract_group(self, group_id: str, output_path: str):
        """Export ``group_id`` as a standalone SVG file."""
        group_elem = self.root.find(
            f".//svg:g[@id='{group_id}']",
            self.namespaces
        )

        if group_elem is None:
            raise ValueError(f"Group '{group_id}' not found in SVG.")

        # Bounding box
        bbox = self.get_group_bounding_box(group_id)
        if bbox is None:
            print(f"[SvgLoader] Impossible to compute bounding box for {group_id}")
            return None

        x_min, y_min, x_max, y_max = bbox

        width = x_max - x_min
        height = y_max - y_min

        # Nouveau SVG racine
        new_svg = ET.Element(
            'svg',
            {
                'xmlns': 'http://www.w3.org/2000/svg',
                'width': str(width),
                'height': str(height),
                'viewBox': f"{x_min} {y_min} {width} {height}",
            },
        )

        # Cloner le groupe original
        cloned_group = ET.fromstring(ET.tostring(group_elem))

        # No path translation; rely on the viewBox
        new_svg.append(cloned_group)

        new_tree = ET.ElementTree(new_svg)
        new_tree.write(output_path)

        print(f"[SvgLoader] Group '{group_id}' exported → {output_path}")

        return x_min, y_min


def translate_path(d, dx, dy):
    """
    Décale toutes les coordonnées d'un path SVG.
    """
    def repl(match):
        nums = match.group(0).strip().split()
        new_nums = []
        for i, n in enumerate(nums):
            try:
                num = float(n)
                if i % 2 == 0:
                    num -= dx
                else:
                    num -= dy
                new_nums.append(str(num))
            except ValueError:
                new_nums.append(n)
        return " ".join(new_nums)

    return re.sub(
        r"((?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?\s*)+)",
        repl,
        d
    )
