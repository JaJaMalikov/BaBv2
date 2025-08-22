"""Module for creating and managing SVG-based icons with dynamic coloring."""

import re
import logging
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, QSize, QSettings, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from .ui_profile import _color, _int
from ui.settings_keys import (
    ORG,
    APP,
    UI_ICON_SIZE,
    UI_ICON_COLOR_NORMAL,
    UI_ICON_COLOR_HOVER,
    UI_ICON_COLOR_ACTIVE,
    UI_ICON_OVERRIDE,
    UI_ICON_DIR,
)

ICONS_DIR = Path("assets/icons")
# Cache keyed by name|size|colors to reflect runtime settings
ICON_CACHE: Dict[str, QIcon] = {}


def _tint_svg(svg: str, color: str) -> str:
    """Return SVG with <path> elements filled with the given color.
    - Removes existing fill attributes and style-based fill on <path> tags.
    - If no <path> tags are present, returns original SVG (graceful fallback).
    """
    try:
        if "<path" not in svg:
            return svg
        # Remove explicit fill attributes on path
        svg2 = re.sub(r"(<path\b[^>]*?)\s+fill=\"[^\"]*\"", r"\\1", svg)
        # Remove style fill declarations inside style="..."
        def _strip_style_fill(m: re.Match[str]) -> str:
            prefix, body, suffix = m.group(1), m.group(2), m.group(3)
            # Remove fill:...; occurrences
            parts = [p for p in body.split(";") if p.strip() and not p.strip().lower().startswith("fill:")]
            new_body = ";".join(parts)
            return f"{prefix}{new_body}{suffix}"
        svg2 = re.sub(r"(<path\b[^>]*?\sstyle=\")([^\"]*)(\")", _strip_style_fill, svg2)
        # Inject our fill
        tinted = re.sub(r"<path\b", f'<path fill="{color}"', svg2)
        return tinted
    except Exception:
        # Safety: return the original SVG if anything goes wrong
        return svg


def _icon_colors() -> tuple[str, str, str]:
    """Read icon colors from settings or return defaults with normalization."""
    try:
        s = QSettings(ORG, APP)
        normal = _color(s.value(UI_ICON_COLOR_NORMAL), "#4A5568")
        hover = _color(s.value(UI_ICON_COLOR_HOVER), "#E53E3E")
        active = _color(s.value(UI_ICON_COLOR_ACTIVE), "#FFFFFF")
        return normal, hover, active
    except (RuntimeError, ValueError):
        logging.exception("Failed to read icon colors from settings")
        return "#4A5568", "#E53E3E", "#FFFFFF"


def _icon_size() -> int:
    """Read preferred icon size from QSettings with normalization; default 32.
    Clamps the value to a sensible range [16, 128].
    """
    try:
        s = QSettings(ORG, APP)
        size = _int(s.value(UI_ICON_SIZE), 32)
        if size < 16:
            size = 16
        elif size > 128:
            size = 128
        return size
    except Exception:
        return 32


def _render_svg(svg_data: str, size: QSize | None = None) -> QPixmap:
    """Render SVG data to a QPixmap of a specific size. Safe against invalid SVG."""
    if size is None:
        side = _icon_size()
        size = QSize(side, side)
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
        s = QSettings(ORG, APP)
        override_path = s.value(UI_ICON_OVERRIDE(name))
    except (RuntimeError, ValueError):
        logging.exception("Failed to read icon overrides")
        return None

    if not override_path:
        return None

    p = Path(str(override_path))
    if not p.exists():
        return None

    try:
        if p.suffix.lower() == ".svg":
            with open(p, "r", encoding="utf-8") as f:
                original_svg = f.read()
            c_norm, c_hover, c_active = _icon_colors()
            normal_svg = _tint_svg(original_svg, c_norm)
            hover_svg = _tint_svg(original_svg, c_hover)
            active_svg = _tint_svg(original_svg, c_active)
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
    """Create a state-aware icon honoring current icon size and colors.

    Caching is keyed by (name, size, colors) to ensure live updates when settings change.
    """
    c_norm, c_hover, c_active = _icon_colors()
    side = _icon_size()
    cache_key = f"{name}|{side}|{c_norm}|{c_hover}|{c_active}"
    if cache_key in ICON_CACHE:
        return ICON_CACHE[cache_key]

    override_icon = _load_override_icon(name)
    if override_icon:
        ICON_CACHE[cache_key] = override_icon
        return override_icon

    s = QSettings(ORG, APP)
    icon_dir_override = s.value(UI_ICON_DIR)

    # Locate in override directory or default assets (SVG expected)
    # Fallback mapping for missing or alias keys. Documented for maintainability.
    # - load -> open
    # - zoom_in/out -> plus/minus
    # - add_light -> plus
    # - toggle_* -> base icon (library/inspector/timeline/custom)
    # - custom -> layers
    # - settings -> layers (robustness when override dir lacks settings.svg)
    # - close -> close_menu (generic close icon)
    fallback_map = {
        "custom": "layers",
        "settings": "settings",
        "close": "delete",
        "load": "open",
        "zoom_in": "plus",
        "zoom_out": "minus",
        "add_light": "plus",
        "toggle_library": "library",
        "toggle_inspector": "inspector",
        "toggle_timeline": "timeline",
        "toggle_custom": "open_menu",
    }
    svg_key = fallback_map.get(name, name)
    svg_path = ICONS_DIR / f"{svg_key}.svg"
    if icon_dir_override:
        alt = Path(str(icon_dir_override)) / f"{svg_key}.svg"
        if alt.exists():
            svg_path = alt
    if not svg_path.exists():
        logging.warning(
            "Icon '%s' not found at %s; falling back to 'warning' icon", name, svg_path
        )
        warn_path = ICONS_DIR / "warning.svg"
        if icon_dir_override:
            alt_warn = Path(str(icon_dir_override)) / "warning.svg"
            if alt_warn.exists():
                warn_path = alt_warn
        if warn_path.exists():
            with open(warn_path, "r", encoding="utf-8") as f:
                original_svg = f.read()
            c_norm, c_hover, c_active = _icon_colors()
            normal_svg = _tint_svg(original_svg, c_norm)
            hover_svg = _tint_svg(original_svg, c_hover)
            active_svg = _tint_svg(original_svg, c_active)
            size = QSize(side, side)
            pixmap_normal = _render_svg(normal_svg, size)
            pixmap_hover = _render_svg(hover_svg, size)
            pixmap_active = _render_svg(active_svg, size)
            icon = QIcon()
            icon.addPixmap(pixmap_normal, QIcon.Normal, QIcon.Off)
            icon.addPixmap(pixmap_hover, QIcon.Active, QIcon.Off)
            icon.addPixmap(pixmap_active, QIcon.Normal, QIcon.On)
            icon.addPixmap(pixmap_active, QIcon.Active, QIcon.On)
            ICON_CACHE[cache_key] = icon
            return icon
        ICON_CACHE[cache_key] = QIcon()
        return QIcon()

    with open(svg_path, "r", encoding="utf-8") as f:
        original_svg = f.read()

    # Create different colored versions using robust tinting
    normal_svg = _tint_svg(original_svg, c_norm)
    hover_svg = _tint_svg(original_svg, c_hover)
    active_svg = _tint_svg(original_svg, c_active)

    # Render pixmaps at the configured size
    size = QSize(side, side)
    pixmap_normal = _render_svg(normal_svg, size)
    pixmap_hover = _render_svg(hover_svg, size)
    pixmap_active = _render_svg(active_svg, size)

    # Create the icon and add pixmaps for each state
    icon = QIcon()
    icon.addPixmap(pixmap_normal, QIcon.Normal, QIcon.Off)
    icon.addPixmap(pixmap_hover, QIcon.Active, QIcon.Off)  # Hover state
    icon.addPixmap(pixmap_active, QIcon.Normal, QIcon.On)  # Checked/On state
    icon.addPixmap(pixmap_active, QIcon.Active, QIcon.On)  # Checked/On + Hover state

    ICON_CACHE[cache_key] = icon
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
    return get_icon("plus")


def icon_minus():
    """Get the minus icon."""
    return get_icon("minus")


def icon_fit():
    """Get the fit icon."""
    return get_icon("fit")


def icon_rotate():
    """Get the rotate icon."""
    return get_icon("rotate")


def icon_chevron_left():
    """Get the chevron_left icon."""
    return get_icon("chevron_left")


def icon_chevron_right():
    """Get the chevron_right icon."""
    return get_icon("chevron_right")


def icon_scene_size():
    """Get the scene_size icon."""
    return get_icon("scene_size")


def icon_background():
    """Get the background icon."""
    return get_icon("background")


def icon_library():
    """Get the library icon."""
    return get_icon("library")


def icon_inspector():
    """Get the inspector icon."""
    return get_icon("inspector")


def icon_timeline():
    """Get the timeline icon."""
    return get_icon("timeline")


def icon_onion():
    """Get the onion icon."""
    return get_icon("onion")


def icon_save():
    """Get the save icon."""
    return get_icon("save")


def icon_open():
    """Get the open icon."""
    return get_icon("open")


def icon_delete():
    """Get the delete icon."""
    return get_icon("delete")


def icon_duplicate():
    """Get the duplicate icon."""
    return get_icon("duplicate")


def icon_link():
    """Get the link icon."""
    return get_icon("link")


def icon_link_off():
    """Get the link_off icon."""
    return get_icon("link_off")


def icon_close():
    """Get the close icon."""
    return get_icon("close")


def icon_objets():
    """Get the objets icon."""
    return get_icon("objets")


def icon_puppet():
    """Get the puppet icon."""
    return get_icon("puppet")


def icon_reset_ui():
    """Get the reset_ui icon."""
    return get_icon("reset_ui")


def icon_reset_scene():
    """Get the new_file icon."""
    return get_icon("new_file")


def icon_open_menu():
    """Get the open_menu icon."""
    return get_icon("open_menu")


def icon_close_menu():
    """Get the close_menu icon."""
    return get_icon("close_menu")


def icon_close_menu_inv():
    """Get the close_menu_inv icon."""
    return get_icon("close_menu_inv")


def icon_settings():
    """Get the settings icon."""
    return get_icon("settings")
