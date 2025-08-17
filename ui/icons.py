"""Module for creating and managing SVG-based icons with dynamic coloring."""

import re
import logging
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, QSize, QSettings, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

ICONS_DIR = Path("assets/icons")
ICON_CACHE: Dict[str, QIcon] = {}

def _icon_colors() -> tuple[str, str, str]:
    """Read icon colors from settings or return defaults."""
    try:
        s = QSettings("JaJa", "Macronotron")
        normal = s.value("ui/icon_color_normal") or "#4A5568"
        hover = s.value("ui/icon_color_hover") or "#E53E3E"
        active = s.value("ui/icon_color_active") or "#FFFFFF"
        return str(normal), str(hover), str(active)
    except (RuntimeError, ValueError):
        logging.exception("Failed to read icon colors from settings")
        return "#4A5568", "#E53E3E", "#FFFFFF"

def _render_svg(svg_data: str, size: QSize = QSize(32, 32)) -> QPixmap:
    """Renders SVG data to a QPixmap of a specific size. Safe against invalid SVG."""
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)
    try:
        data = QByteArray(svg_data.encode("utf-8"))
        renderer = QSvgRenderer(data)
        if not renderer.isValid():
            return pixmap
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
    except Exception:
        # Return transparent pixmap on failure
        pass
    return pixmap

def _load_override_icon(name: str) -> Optional[QIcon]:
    """Load an icon from an override path if specified in QSettings."""
    try:
        s = QSettings("JaJa", "Macronotron")
        override_path = s.value(f"ui/icon_override/{name}")
    except (RuntimeError, ValueError):
        logging.exception("Failed to read icon overrides")
        return None

    if not override_path:
        return None

    p = Path(str(override_path))
    if not p.exists():
        return None

    try:
        if p.suffix.lower() == '.svg':
            with open(p, 'r', encoding="utf-8") as f:
                original_svg = f.read()
            c_norm, c_hover, c_active = _icon_colors()
            normal_svg = re.sub(r'<path', f'<path fill="{c_norm}"', original_svg)
            hover_svg = re.sub(r'<path', f'<path fill="{c_hover}"', original_svg)
            active_svg = re.sub(r'<path', f'<path fill="{c_active}"', original_svg)
            pixmap_normal = _render_svg(normal_svg)
            pixmap_hover = _render_svg(hover_svg)
            pixmap_active = _render_svg(active_svg)
            icon = QIcon()
            icon.addPixmap(pixmap_normal, QIcon.Normal, QIcon.Off)
            icon.addPixmap(pixmap_hover, QIcon.Active, QIcon.Off)
            icon.addPixmap(pixmap_active, QIcon.Normal, QIcon.On)
            icon.addPixmap(pixmap_active, QIcon.Active, QIcon.On)
            return icon

        # Bitmap path: use same image for all states
        pix = QPixmap(str(p))
        return QIcon(pix)

    except (OSError, ValueError, RuntimeError) as e:
        logging.warning("Failed loading override for %s: %s", name, e)
        return None

def _create_icon(name: str) -> QIcon:
    """Creates a state-aware icon with different colors for normal, hover, and active states."""
    if name in ICON_CACHE:
        return ICON_CACHE[name]

    override_icon = _load_override_icon(name)
    if override_icon:
        ICON_CACHE[name] = override_icon
        return override_icon

    s = QSettings("JaJa", "Macronotron")
    icon_dir_override = s.value("ui/icon_dir")

    # Otherwise, locate in override directory or default assets (SVG expected)
    # Provide fallback mapping for missing keys
    fallback_map = {
        "custom": "layers",
        "settings": "layers",
    }
    svg_key = fallback_map.get(name, name)
    svg_path = ICONS_DIR / f"{svg_key}.svg"
    if icon_dir_override:
        alt = Path(str(icon_dir_override)) / f"{svg_key}.svg"
        if alt.exists():
            svg_path = alt
    if not svg_path.exists():
        logging.debug("Icon '%s' not found at %s", name, svg_path)
        ICON_CACHE[name] = QIcon()  # Cache empty icon if not found
        return QIcon()

    with open(svg_path, 'r', encoding="utf-8") as f:
        original_svg = f.read()

    # Create different colored versions
    c_norm, c_hover, c_active = _icon_colors()
    normal_svg = re.sub(r'<path', f'<path fill="{c_norm}"', original_svg)
    hover_svg = re.sub(r'<path', f'<path fill="{c_hover}"', original_svg)
    active_svg = re.sub(r'<path', f'<path fill="{c_active}"', original_svg)

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
    """Get an icon by name."""
    return _create_icon(name)

def clear_cache() -> None:
    """Clear in-memory icon cache so future calls reload with new settings."""
    ICON_CACHE.clear()

# Compatibility layer
def icon_plus():
    """Get the plus icon."""
    return get_icon('plus')
def icon_minus():
    """Get the minus icon."""
    return get_icon('minus')
def icon_fit():
    """Get the fit icon."""
    return get_icon('fit')
def icon_rotate():
    """Get the rotate icon."""
    return get_icon('rotate')
def icon_chevron_left():
    """Get the chevron_left icon."""
    return get_icon('chevron_left')
def icon_chevron_right():
    """Get the chevron_right icon."""
    return get_icon('chevron_right')
def icon_scene_size():
    """Get the scene_size icon."""
    return get_icon('scene_size')
def icon_background():
    """Get the background icon."""
    return get_icon('background')
def icon_library():
    """Get the library icon."""
    return get_icon('library')
def icon_inspector():
    """Get the inspector icon."""
    return get_icon('inspector')
def icon_timeline():
    """Get the timeline icon."""
    return get_icon('timeline')
def icon_onion():
    """Get the onion icon."""
    return get_icon('onion')
def icon_save():
    """Get the save icon."""
    return get_icon('save')
def icon_open():
    """Get the open icon."""
    return get_icon('open')
def icon_delete():
    """Get the delete icon."""
    return get_icon('delete')
def icon_duplicate():
    """Get the duplicate icon."""
    return get_icon('duplicate')
def icon_link():
    """Get the link icon."""
    return get_icon('link')
def icon_link_off():
    """Get the link_off icon."""
    return get_icon('link_off')
def icon_close():
    """Get the close icon."""
    return get_icon('close')
def icon_objets():
    """Get the objets icon."""
    return get_icon('objets')
def icon_puppet():
    """Get the puppet icon."""
    return get_icon('puppet')
def icon_reset_ui():
    """Get the reset_ui icon."""
    return get_icon('reset_ui')
def icon_reset_scene():
    """Get the new_file icon."""
    return get_icon('new_file')
def icon_open_menu():
    """Get the open_menu icon."""
    return get_icon('open_menu')
def icon_close_menu():
    """Get the close_menu icon."""
    return get_icon('close_menu')
def icon_close_menu_inv():
    """Get the close_menu_inv icon."""
    return get_icon('close_menu_inv')
def icon_settings():
    """Get the settings icon."""
    return get_icon('settings')
