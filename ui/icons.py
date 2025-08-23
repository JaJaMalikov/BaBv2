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
            parts = [
                p
                for p in body.split(";")
                if p.strip() and not p.strip().lower().startswith("fill:")
            ]
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
        logging.warning("Icon override for %s set to missing path: %s", name, p)
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


def get_icon(name: str) -> QIcon:
    """Get an icon by name."""
    return _create_icon(name)


def clear_cache() -> None:
    """Clear in-memory icon cache so future calls reload with new settings."""
    ICON_CACHE.clear()


# Legacy compatibility -----------------------------------------------------
# ``icon_*`` helpers previously exposed individual functions for each icon.
# They have been removed in favour of :func:`get_icon`.  The mapping below
# is used by ``__getattr__`` to lazily provide deprecated wrappers for any
# remaining imports.

LEGACY_ICON_ALIASES = {
    "reset_scene": "new_file",
}


def __getattr__(name: str):  # pragma: no cover - simple delegation
    """Resolve deprecated ``icon_*`` helpers on demand.

    Accessing ``icon_plus`` will emit a deprecation warning and return a
    callable equivalent to ``lambda: get_icon("plus")``.  Unknown attributes
    fall back to normal ``AttributeError`` behaviour.
    """
    import warnings

    if name.startswith("icon_"):
        key = name[5:]
        key = LEGACY_ICON_ALIASES.get(key, key)
        warnings.warn(
            f"{name} is deprecated; use get_icon('{key}')",  # noqa: B028
            DeprecationWarning,
            stacklevel=2,
        )
        return lambda: get_icon(key)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
