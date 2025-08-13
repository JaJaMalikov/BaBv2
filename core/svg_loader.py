from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Optional, Tuple, Dict

from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QRectF


_COORD_PATTERN = re.compile(
    r"((?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?\s*)+)"
)


class SvgLoader:
    def __init__(self, svg_path: str) -> None:
        self.svg_path: str = svg_path
        self.tree: ET.ElementTree = ET.parse(svg_path)
        self.root: ET.Element = self.tree.getroot()
        self.namespaces: Dict[str, str] = {"svg": "http://www.w3.org/2000/svg"}
        self.renderer: QSvgRenderer = QSvgRenderer(svg_path)

    def get_group_offset(self, group_id: str) -> Optional[Tuple[float, float]]:
        """Return the top-left coordinates of ``group_id``."""

        rect: QRectF = self.renderer.boundsOnElement(group_id)
        if rect.isNull():
            return None

        return rect.left(), rect.top()

    def get_groups(self) -> List[str]:
        groups: List[str] = []
        for elem in self.root.findall(".//svg:g", self.namespaces):
            group_id: Optional[str] = elem.attrib.get("id")
            if group_id:
                groups.append(group_id)
        return groups

    def get_group_bounding_box(self, group_id: str) -> Optional[Tuple[float, float, float, float]]:
        """Return the bounding box of ``group_id``."""

        rect: QRectF = self.renderer.boundsOnElement(group_id)
        if rect.isNull():
            return None

        return (rect.left(), rect.top(), rect.right(), rect.bottom())

    def get_pivot(self, group_id: str) -> Tuple[float, float]:
        """
        Retourne le centre de la bbox du groupe (pour les groupes pivot).
        """
        bbox: Optional[Tuple[float, float, float, float]] = self.get_group_bounding_box(group_id)
        if bbox is None:
            return 0.0, 0.0 # Return floats for consistency
        x_min, y_min, x_max, y_max = bbox
        cx: float = (x_min + x_max) / 2
        cy: float = (y_min + y_max) / 2
        return cx, cy

    def extract_group(self, group_id: str, output_path: str) -> Optional[Tuple[float, float]]:
        """Export ``group_id`` as a standalone SVG file."""
        group_elem: Optional[ET.Element] = self.root.find(
            f".//svg:g[@id='{group_id}']",
            self.namespaces
        )

        if group_elem is None:
            raise ValueError(f"Group '{group_id}' not found in SVG.")

        # Bounding box
        bbox: Optional[Tuple[float, float, float, float]] = self.get_group_bounding_box(group_id)
        if bbox is None:
            logging.warning(f"Impossible to compute bounding box for SVG group: {group_id}")
            return None

        x_min, y_min, x_max, y_max = bbox

        width: float = x_max - x_min
        height: float = y_max - y_min

        # Nouveau SVG racine
        new_svg: ET.Element = ET.Element(
            'svg',
            {
                'xmlns': 'http://www.w3.org/2000/svg',
                'width': str(width),
                'height': str(height),
                'viewBox': f"{x_min} {y_min} {width} {height}",
            },
        )

        # Cloner le groupe original
        cloned_group: ET.Element = ET.fromstring(ET.tostring(group_elem))

        # No path translation; rely on the viewBox
        new_svg.append(cloned_group)

        new_tree: ET.ElementTree = ET.ElementTree(new_svg)
        new_tree.write(output_path)
        logging.info("[SvgLoader] Group '%s' exported → %s", group_id, output_path)

        return x_min, y_min

    def get_svg_viewbox(self) -> List[float]:
        viewbox: Optional[str] = self.root.attrib.get("viewBox")
        if viewbox:
            return [float(x) for x in viewbox.strip().split()]
        # Fallback : width/height (mais pas toujours fiable)
        width: float = float(self.root.attrib.get("width", 0.0))
        height: float = float(self.root.attrib.get("height", 0.0))
        return [0.0, 0.0, width, height]

def translate_path(d: str, dx: float, dy: float) -> str:
    """
    Décale toutes les coordonnées d'un path SVG.
    """
    def repl(match: re.Match) -> str:
        nums: List[str] = match.group(0).strip().split()
        new_nums: List[str] = []
        for i, n in enumerate(nums):
            try:
                num: float = float(n)
                if i % 2 == 0:
                    num -= dx
                else:
                    num -= dy
                new_nums.append(str(num))
            except ValueError:
                new_nums.append(n) # Keep non-numeric parts as is
        return " ".join(new_nums)

    return _COORD_PATTERN.sub(repl, d)
