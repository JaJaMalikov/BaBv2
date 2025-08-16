"""Utilities to inspect and extract data from SVG files."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple


from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QRectF


# Types parlants
Point = Tuple[float, float]
BoundingBox = Tuple[float, float, float, float]

# Constantes SVG
SVG_NS: str = "http://www.w3.org/2000/svg"
DEFAULT_NAMESPACES: Dict[str, str] = {"svg": SVG_NS}


class SvgLoader:
    """Load an SVG document and provide helpers to inspect its groups."""

    def __init__(self, svg_path: str) -> None:
        """Initialize loader and parse the SVG file at ``svg_path``."""
        self.svg_path: str = svg_path
        self.tree: ET.ElementTree = ET.parse(svg_path)
        self.root: ET.Element = self.tree.getroot()
        self.namespaces: Dict[str, str] = DEFAULT_NAMESPACES
        self.renderer: QSvgRenderer = QSvgRenderer(svg_path)

    # -------------------------
    # Helpers privés
    # -------------------------
    def _get_bounds_rect(self, element_id: str) -> Optional[QRectF]:
        """Retourne le QRectF des bounds pour un élément identifié.

        Retourne None si non trouvé/invalide.
        """
        bounds_rect: QRectF = self.renderer.boundsOnElement(element_id)
        if bounds_rect.isNull():
            return None
        return bounds_rect

    @staticmethod
    def _rect_to_bbox(rect: QRectF) -> BoundingBox:
        """Convertit un QRectF en BoundingBox (x_min, y_min, x_max, y_max)."""
        return rect.left(), rect.top(), rect.right(), rect.bottom()

    @staticmethod
    def _clone_element(elem: ET.Element) -> ET.Element:
        """Clone un élément XML (shallow copy structure)."""
        return ET.fromstring(ET.tostring(elem))

    # -------------------------
    # API publique
    # -------------------------
    def get_group_offset(self, group_id: str) -> Optional[Point]:
        """Retourne les coordonnées (x, y) du coin haut-gauche du groupe."""
        bounds_rect: Optional[QRectF] = self._get_bounds_rect(group_id)
        if bounds_rect is None:
            return None
        return bounds_rect.left(), bounds_rect.top()

    def get_groups(self) -> List[str]:
        """List the identifiers of all ``<g>`` groups."""
        return [
            elem.attrib["id"]
            for elem in self.root.findall(".//svg:g", self.namespaces)
            if "id" in elem.attrib
        ]

    def get_group_bounding_box(self, group_id: str) -> Optional[BoundingBox]:
        """Retourne la bounding box (x_min, y_min, x_max, y_max) du groupe."""
        bounds_rect: Optional[QRectF] = self._get_bounds_rect(group_id)
        if bounds_rect is None:
            return None
        return self._rect_to_bbox(bounds_rect)

    def get_pivot(self, group_id: str) -> Point:
        """Return the center of a group's bounding box (pivot)."""
        bounding_box: Optional[BoundingBox] = self.get_group_bounding_box(group_id)
        if bounding_box is None:
            return 0.0, 0.0  # Cohérence: toujours des floats
        x_min, y_min, x_max, y_max = bounding_box
        cx: float = (x_min + x_max) / 2
        cy: float = (y_min + y_max) / 2
        return cx, cy

    def extract_group(self, group_id: str, output_path: str) -> Optional[Point]:
        """Export ``group_id`` into a standalone SVG file and return its offset."""
        group_elem: Optional[ET.Element] = self.root.find(
            f".//svg:g[@id='{group_id}']",
            self.namespaces,
        )
        if group_elem is None:
            raise ValueError(f"Group '{group_id}' not found in SVG.")

        # Bounding box
        bounding_box: Optional[BoundingBox] = self.get_group_bounding_box(group_id)
        if bounding_box is None:
            logging.warning("Impossible de calculer la bounding box du groupe SVG: %s", group_id)
            return None

        x_min, y_min, x_max, y_max = bounding_box
        width: float = x_max - x_min
        height: float = y_max - y_min

        # Nouveau SVG racine (on s'appuie sur le viewBox pour le cadrage)
        new_svg: ET.Element = ET.Element(
            "svg",
            {
                "xmlns": SVG_NS,
                "width": str(width),
                "height": str(height),
                "viewBox": f"{x_min} {y_min} {width} {height}",
            },
        )

        cloned_group: ET.Element = self._clone_element(group_elem)
        new_svg.append(cloned_group)

        new_tree: ET.ElementTree = ET.ElementTree(new_svg)
        new_tree.write(output_path)
        logging.info("[SvgLoader] Group '%s' exported → %s", group_id, output_path)

        return x_min, y_min

    def get_svg_viewbox(self) -> List[float]:
        """Return the SVG viewBox as ``[min_x, min_y, width, height]``.

        If the viewBox is missing, fall back to width/height attributes and
        return ``[0.0, 0.0, 0.0, 0.0]`` when values are unavailable.
        """
        viewbox: Optional[str] = self.root.attrib.get("viewBox")
        if viewbox:
            parts = viewbox.strip().split()
            if len(parts) == 4:
                try:
                    return [float(x) for x in parts]
                except ValueError:
                    pass  # On retombe sur le fallback ci-dessous

        # Fallback : width/height (peu fiable si unités)
        def _to_float_maybe_unit(val: str, default: float = 0.0) -> float:
            try:
                return float(val)
            except (TypeError, ValueError):
                # Essaye de retirer d'éventuelles unités (px, etc.)
                if isinstance(val, str):
                    num = "".join(ch for ch in val if (ch.isdigit() or ch in ".-+eE"))
                    try:
                        return float(num)
                    except ValueError:
                        return default
                return default

        width: float = _to_float_maybe_unit(self.root.attrib.get("width", "0"))
        height: float = _to_float_maybe_unit(self.root.attrib.get("height", "0"))
        return [0.0, 0.0, width, height]
