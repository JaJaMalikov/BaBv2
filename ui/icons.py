"""Module for creating and managing SVG-based icons with dynamic coloring."""

import re
import logging
from pathlib import Path
from typing import Dict

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QSettings

ICONS_DIR = Path("assets/icons")
ICON_CACHE: Dict[str, QIcon] = {}

# Define colors from our theme
COLOR_NORMAL = "#4A5568"
COLOR_HOVER = "#E53E3E"
COLOR_ACTIVE = "#FFFFFF"

def _render_svg(svg_data: str, size: QSize = QSize(32, 32)) -> QPixmap:
    """Renders SVG data to a QPixmap of a specific size."""
    renderer = QSvgRenderer(svg_data.encode("utf-8"))
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap

def _create_icon(name: str) -> QIcon:
    """Creates a state-aware icon with different colors for normal, hover, and active states."""
    if name in ICON_CACHE:
        return ICON_CACHE[name]

    # Optional per-icon override path from QSettings
    try:
        s = QSettings("JaJa", "Macronotron")
        override_path = s.value(f"ui/icon_override/{name}")
        icon_dir_override = s.value("ui/icon_dir")
    except Exception:
        override_path = None
        icon_dir_override = None

    # If a direct override path is set, load it (supports SVG and bitmap)
    if override_path:
        p = Path(str(override_path))
        if p.exists():
            try:
                if p.suffix.lower() == '.svg':
                    with open(p, 'r') as f:
                        original_svg = f.read()
                    normal_svg = re.sub(r'<path', f'<path fill="{COLOR_NORMAL}"', original_svg)
                    hover_svg = re.sub(r'<path', f'<path fill="{COLOR_HOVER}"', original_svg)
                    active_svg = re.sub(r'<path', f'<path fill="{COLOR_ACTIVE}"', original_svg)
                    pixmap_normal = _render_svg(normal_svg)
                    pixmap_hover = _render_svg(hover_svg)
                    pixmap_active = _render_svg(active_svg)
                    icon = QIcon()
                    icon.addPixmap(pixmap_normal, QIcon.Normal, QIcon.Off)
                    icon.addPixmap(pixmap_hover, QIcon.Active, QIcon.Off)
                    icon.addPixmap(pixmap_active, QIcon.Normal, QIcon.On)
                    icon.addPixmap(pixmap_active, QIcon.Active, QIcon.On)
                    ICON_CACHE[name] = icon
                    return icon
                else:
                    # Bitmap path: use same image for all states
                    pix = QPixmap(str(p))
                    icon = QIcon(pix)
                    ICON_CACHE[name] = icon
                    return icon
            except Exception as e:
                logging.warning("Failed loading override for %s: %s", name, e)

    # Otherwise, locate in override directory or default assets (SVG expected)
    svg_path = ICONS_DIR / f"{name}.svg"
    if icon_dir_override:
        alt = Path(str(icon_dir_override)) / f"{name}.svg"
        if alt.exists():
            svg_path = alt
    if not svg_path.exists():
        logging.debug("Icon '%s' not found at %s", name, svg_path)
        ICON_CACHE[name] = QIcon()  # Cache empty icon if not found
        return QIcon()

    with open(svg_path, 'r') as f:
        original_svg = f.read()

    # Create different colored versions
    normal_svg = re.sub(r'<path', f'<path fill="{COLOR_NORMAL}"', original_svg)
    hover_svg = re.sub(r'<path', f'<path fill="{COLOR_HOVER}"', original_svg)
    active_svg = re.sub(r'<path', f'<path fill="{COLOR_ACTIVE}"', original_svg)

    # Render pixmaps
    pixmap_normal = _render_svg(normal_svg)
    pixmap_hover = _render_svg(hover_svg)
    pixmap_active = _render_svg(active_svg)

    # Create the icon and add pixmaps for each state
    icon = QIcon()
    icon.addPixmap(pixmap_normal, QIcon.Normal, QIcon.Off)
    icon.addPixmap(pixmap_hover, QIcon.Active, QIcon.Off)  # Hover state
    icon.addPixmap(pixmap_active, QIcon.Normal, QIcon.On)  # Checked/On state
    icon.addPixmap(pixmap_active, QIcon.Active, QIcon.On)  # Checked/On + Hover state

    ICON_CACHE[name] = icon
    return icon

# --- Public Icon Functions ---
# We now use a single function to create all icons.
# The old functions are kept for compatibility but should be phased out.

def get_icon(name: str) -> QIcon:
    return _create_icon(name)

def clear_cache() -> None:
    """Clear in-memory icon cache so future calls reload with new settings."""
    ICON_CACHE.clear()

# Compatibility layer
def icon_plus(): return get_icon('plus')
def icon_minus(): return get_icon('minus')
def icon_fit(): return get_icon('fit')
def icon_rotate(): return get_icon('rotate')
def icon_chevron_left(): return get_icon('chevron_left')
def icon_chevron_right(): return get_icon('chevron_right')
def icon_scene_size(): return get_icon('scene_size')
def icon_background(): return get_icon('background')
def icon_library(): return get_icon('library')
def icon_inspector(): return get_icon('inspector')
def icon_timeline(): return get_icon('timeline')
def icon_onion(): return get_icon('onion')
def icon_save(): return get_icon('save')
def icon_open(): return get_icon('open')
def icon_delete(): return get_icon('delete')
def icon_duplicate(): return get_icon('duplicate')
def icon_link(): return get_icon('link')
def icon_link_off(): return get_icon('link_off')
def icon_close(): return get_icon('close')
def icon_objets(): return get_icon('objets')
def icon_puppet(): return get_icon('puppet')
def icon_reset_ui(): return get_icon('reset_ui')
def icon_reset_scene(): return get_icon('new_file')
def icon_open_menu(): return get_icon('open_menu')
def icon_close_menu(): return get_icon('close_menu')
def icon_close_menu_inv(): return get_icon('close_menu_inv')
def icon_settings(): return get_icon('settings')
