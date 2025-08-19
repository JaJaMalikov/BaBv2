"""Utilities to inspect and extract data from SVG files."""

from __future__ import annotations

import logging
import os
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
    """Load an SVG document and provide helpers to inspect its groups.

    Guards (docs/tasks.md Task 5.31):
    - Validates that the parsed document has an <svg> root element.
    - Raises ValueError for obviously malformed files early.

    Caching and lazy init (docs/tasks.md Task 5.30):
    - ``QSvgRenderer`` instances are cached per file path with a modification time (mtime) key.
    - The renderer is created lazily on first access via the ``renderer`` property.
    - Cache entries are refreshed automatically when the file on disk changes.
    """

    # Renderer cache keyed by svg_path -> (mtime, QSvgRenderer)
    _renderer_cache: Dict[str, Tuple[float, QSvgRenderer]] = {}

    def __init__(self, svg_path: str) -> None:
        """Initialize loader and parse the SVG file at ``svg_path``.

        Raises:
            ValueError: If the file does not contain a valid SVG root element.
        """
        self.svg_path: str = svg_path
        self.tree: ET.ElementTree = ET.parse(svg_path)
        self.root: ET.Element = self.tree.getroot()
        # Basic root guard: ElementTree encodes namespaced tag as '{ns}svg'
        root_tag = self.root.tag.split("}")[-1] if "}" in self.root.tag else self.root.tag
        if root_tag.lower() != "svg":
            raise ValueError(f"Invalid SVG root element: '{self.root.tag}'")
        # Normalize namespace handling (docs/tasks.md Task 5.29):
        # - If the root is namespaced, register that namespace under the 'svg' prefix
        # - If not, we keep an empty mapping and fallback to non-namespaced queries
        if "}" in self.root.tag:
            ns_uri = self.root.tag.split("}")[0][1:]
            self.namespaces: Dict[str, str] = {"svg": ns_uri}
            self._has_namespace = True
        else:
            self.namespaces = {}
            self._has_namespace = False
        # Lazy renderer initialization; see renderer property for cache (Task 5.30)

    @classmethod
    def from_parsed(cls, svg_path: str, tree: ET.ElementTree) -> "SvgLoader":
        """Create a loader from a pre-parsed ElementTree.

        This helper allows parsing XML off the UI thread and constructing the loader
        in the main thread without re-parsing. The QSvgRenderer will still be created
        lazily on first access to ``renderer`` (on the calling thread).
        """
        self = cls.__new__(cls)  # type: ignore[misc]
        self.svg_path = svg_path
        self.tree = tree
        self.root = tree.getroot()
        # Basic root guard
        root_tag = self.root.tag.split("}")[-1] if "}" in self.root.tag else self.root.tag
        if root_tag.lower() != "svg":
            raise ValueError(f"Invalid SVG root element: '{self.root.tag}'")
        if "}" in self.root.tag:
            ns_uri = self.root.tag.split("}")[0][1:]
            self.namespaces = {"svg": ns_uri}
            self._has_namespace = True
        else:
            self.namespaces = {}
            self._has_namespace = False
        return self

    @property
    def renderer(self) -> QSvgRenderer:
        """Lazily construct and cache a QSvgRenderer for this SVG path.

        Caching strategy (docs/tasks.md Task 5.30):
        - Cache key is the SVG file path with its current modification time (mtime).
        - If the file changes on disk, the cache is refreshed automatically.
        """
        try:
            mtime: float = os.path.getmtime(self.svg_path)
        except OSError:
            # If we cannot stat the file, use a sentinel to avoid crashes; still build a renderer.
            mtime = -1.0
        cache_entry = SvgLoader._renderer_cache.get(self.svg_path)
        if cache_entry is None or cache_entry[0] != mtime:
            renderer = QSvgRenderer(self.svg_path)
            SvgLoader._renderer_cache[self.svg_path] = (mtime, renderer)
            return renderer
        return cache_entry[1]

    @classmethod
    def invalidate_cache(cls, svg_path: Optional[str] = None) -> None:
        """Invalidate the renderer cache for a single path or all.

        - svg_path=None clears the whole cache.
        - svg_path set clears only that entry (no error if missing).
        """
        if svg_path is None:
            cls._renderer_cache.clear()
        else:
            cls._renderer_cache.pop(svg_path, None)

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
        """List the identifiers of all ``<g>`` groups.

        Supports both namespaced (svg:g) and non-namespaced (g) SVGs.
        """
        elems: List[ET.Element] = []
        try:
            elems.extend(self.root.findall(".//svg:g", self.namespaces))
        except Exception:  # very defensive; ElementTree findall is usually safe
            pass
        # Fallback: non-namespaced
        elems.extend(self.root.findall(".//g"))
        ids = []
        seen = set()
        for elem in elems:
            _id = elem.attrib.get("id")
            if _id and _id not in seen:
                seen.add(_id)
                ids.append(_id)
        return ids

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
        """Export ``group_id`` into a standalone SVG file and return its offset.

        Tries namespaced lookup first, then falls back to non-namespaced.
        """
        group_elem: Optional[ET.Element] = self.root.find(
            f".//svg:g[@id='{group_id}']",
            self.namespaces,
        )
        if group_elem is None:
            # Fallback: non-namespaced search
            group_elem = self.root.find(f".//g[@id='{group_id}']")
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

        If the viewBox is missing, fall back to width/height attributes. Units:
        - Bare numbers and ``px`` are parsed as floats.
        - Percentages (e.g., ``100%``) are ambiguous without a viewBox; we log a warning and fall back to 0.0.
        - Other units: we attempt to parse the numeric part and log at DEBUG level.
        """
        viewbox: Optional[str] = self.root.attrib.get("viewBox")
        if viewbox:
            parts = viewbox.replace(",", " ").split()
            if len(parts) == 4:
                try:
                    return [float(x) for x in parts]
                except ValueError:
                    logging.warning(
                        "[SvgLoader] Invalid viewBox values: %s; falling back to width/height",
                        viewbox,
                    )
            else:
                logging.warning(
                    "[SvgLoader] Malformed viewBox '%s' (expected 4 values); falling back to width/height",
                    viewbox,
                )

        # Fallback : width/height with unit handling (docs/tasks.md Task 5.29)
        def _parse_length(val: Optional[str], default: float = 0.0) -> float:
            if val is None:
                return default
            s = str(val).strip()
            if not s:
                return default
            if s.endswith("%"):
                logging.warning(
                    "[SvgLoader] Percentage length '%s' without viewBox context; using %.1f as fallback",
                    s,
                    default,
                )
                return default
            if s.endswith("px"):
                s = s[:-2]
            try:
                return float(s)
            except ValueError:
                # Strip non-numeric characters as a lenient fallback
                num = "".join(ch for ch in s if (ch.isdigit() or ch in ".-+eE"))
                try:
                    return float(num)
                except ValueError:
                    logging.debug(
                        "[SvgLoader] Could not parse length '%s'; using default %.1f", s, default
                    )
                    return default

        width: float = _parse_length(self.root.attrib.get("width"), 0.0)
        height: float = _parse_length(self.root.attrib.get("height"), 0.0)
        return [0.0, 0.0, width, height]
