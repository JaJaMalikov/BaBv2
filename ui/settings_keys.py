"""Centralized QSettings keys and helpers.

This module defines the stable keys used throughout the app to access QSettings.
Refer to .junie/guidelines.md for the authoritative list and semantics.

Use these constants/functions to avoid key drift and typos. Keep names
UPPER_CASE and group-related helpers together.
"""

from __future__ import annotations

from typing import Final, Any, Dict, List, Tuple, Optional as _Optional
from PySide6.QtCore import QSettings as _QSettings
# Scope
ORG: Final = "JaJa"
APP: Final = "Macronotron"

# Geometry and layout
GEOMETRY_MAINWINDOW: Final = "geometry/mainwindow"
GEOMETRY_LIBRARY: Final = "geometry/library"
GEOMETRY_INSPECTOR: Final = "geometry/inspector"
GEOMETRY_VIEW_TOOLBAR: Final = "geometry/view_toolbar"
GEOMETRY_MAIN_TOOLBAR: Final = "geometry/main_toolbar"

LAYOUT_TIMELINE_VISIBLE: Final = "layout/timeline_visible"

# UI theme and style
UI_ICON_DIR: Final = "ui/icon_dir"
UI_ICON_SIZE: Final = "ui/icon_size"
UI_THEME: Final = "ui/theme"
UI_THEME_FILE: Final = "ui/theme_file"
UI_FONT_FAMILY: Final = "ui/font_family"
UI_STYLE_SCENE_BG: Final = "ui/style/scene_bg"
UI_CUSTOM_STYLESHEET: Final = "ui/custom_stylesheet"
# Misc UI defaults (overlay geometry helpers)
UI_DEFAULT_CUSTOM_SIZE: Final = "ui/default/custom_size"
UI_DEFAULT_CUSTOM_POS: Final = "ui/default/custom_pos"
UI_DEFAULT_PREFIX: Final = "ui/default/"


def UI_DEFAULT_SIZE(name: str) -> str:
    return f"{UI_DEFAULT_PREFIX}{name}_size"


def UI_DEFAULT_POS(name: str) -> str:
    return f"{UI_DEFAULT_PREFIX}{name}_pos"


# Theme custom params (prefix)
UI_CUSTOM_PARAMS_PREFIX: Final = "ui/custom_params/"
UI_CUSTOM_PARAMS_GROUP: Final = "ui/custom_params"


def UI_CUSTOM_PARAM(key: str) -> str:
    return f"{UI_CUSTOM_PARAMS_PREFIX}{key}"


# Icon overrides and colors
UI_ICON_OVERRIDE_PREFIX: Final = "ui/icon_override/"
UI_ICON_OVERRIDE_GROUP: Final = "ui/icon_override"


def UI_ICON_OVERRIDE(name: str) -> str:
    return f"{UI_ICON_OVERRIDE_PREFIX}{name}"


UI_ICON_COLOR_NORMAL: Final = "ui/icon_color_normal"
UI_ICON_COLOR_HOVER: Final = "ui/icon_color_hover"
UI_ICON_COLOR_ACTIVE: Final = "ui/icon_color_active"

# Menus (orders and visibility)
UI_MENU_PREFIX: Final = "ui/menu/"

MAIN_MENU: Final = "main"
QUICK_MENU: Final = "quick"
CUSTOM_MENU: Final = "custom"


def UI_MENU_ORDER(prefix: str) -> str:
    return f"{UI_MENU_PREFIX}{prefix}/order"


def UI_MENU_VIS(prefix: str, action_key: str) -> str:
    return f"{UI_MENU_PREFIX}{prefix}/{action_key}"


UI_MENU_CUSTOM_VISIBLE: Final = "ui/menu/custom/visible"

# Timeline theming colors
TIMELINE_BG: Final = "timeline/bg"
TIMELINE_RULER_BG: Final = "timeline/ruler_bg"
TIMELINE_TRACK_BG: Final = "timeline/track_bg"
TIMELINE_TICK: Final = "timeline/tick"
TIMELINE_TICK_MAJOR: Final = "timeline/tick_major"
TIMELINE_PLAYHEAD: Final = "timeline/playhead"
TIMELINE_KF: Final = "timeline/kf"
TIMELINE_KF_HOVER: Final = "timeline/kf_hover"
TIMELINE_INOUT_ALPHA: Final = "timeline/inout_alpha"

# Scene persisted preferences
SCENE_WIDTH: Final = "scene/width"
SCENE_HEIGHT: Final = "scene/height"

# Shortcuts
SHORTCUTS_PREFIX: Final = "shortcuts/"


def SHORTCUT_KEY(action_key: str) -> str:
    return f"{SHORTCUTS_PREFIX}{action_key}"


# NOTE: This file centralizes all QSettings keys used across the app.
# Keep additions scoped and consistent with .junie/guidelines.md

# Onion skin settings
ONION_PREV_COUNT: Final = "onion/prev_count"
ONION_NEXT_COUNT: Final = "onion/next_count"
ONION_OPACITY_PREV: Final = "onion/opacity_prev"
ONION_OPACITY_NEXT: Final = "onion/opacity_next"


# --- UISettings façade -----------------------------------------------------
def _b(v: Any, default: bool = False) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return bool(default)
    try:
        s = str(v).strip().lower()
        if s in {"1", "true", "yes", "on"}:
            return True
        if s in {"0", "false", "no", "off"}:
            return False
    except Exception:
        pass
    return bool(default)


def _i(v: Any, default: int = 0) -> int:
    try:
        if v is None:
            return int(default)
        if isinstance(v, (int,)):
            return int(v)
        if isinstance(v, float):
            return int(v)
        return int(str(v).strip())
    except Exception:
        return int(default)


def _csv_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v if str(x)]
    return [s for s in str(v).split(",") if s]


class UISettings:
    """Lightweight façade over QSettings for controllers and adapters.

    - Provides typed getters with normalization (bool/int/CSV) and sensible defaults.
    - Keeps QSettings use confined to ui/ layer; controllers can be given an instance.
    """

    def __init__(self, settings: _Optional[_QSettings] = None) -> None:
        self._s = settings or _QSettings(ORG, APP)

    # --- Icon/theme -----------------------------------------------------
    def icon_dir(self) -> str | None:
        v = self._s.value(UI_ICON_DIR)
        return str(v) if v else None

    def icon_size(self, default: int = 32) -> int:
        return _i(self._s.value(UI_ICON_SIZE, default), default)

    def icon_colors(self) -> Tuple[str, str, str]:
        n = str(self._s.value(UI_ICON_COLOR_NORMAL) or "#222222")
        h = str(self._s.value(UI_ICON_COLOR_HOVER) or "#333333")
        a = str(self._s.value(UI_ICON_COLOR_ACTIVE) or "#0078d4")
        return n, h, a

    def icon_override(self, name: str) -> str | None:
        v = self._s.value(UI_ICON_OVERRIDE(name))
        return str(v) if v else None

    # --- Menus/overlays -------------------------------------------------
    def menu_order(
        self, prefix: str, default_order: List[str] | None = None
    ) -> List[str]:
        v = self._s.value(UI_MENU_ORDER(prefix))
        if v is None:
            return list(default_order or [])
        order = _csv_list(v)
        return order if order else list(default_order or [])

    def menu_visibility(self, prefix: str, keys: List[str]) -> Dict[str, bool]:
        vis: Dict[str, bool] = {}
        for k in keys:
            vis[k] = _b(self._s.value(UI_MENU_VIS(prefix, k)), True)
        return vis

    def custom_overlay_visible(self, default: bool = False) -> bool:
        return _b(self._s.value(UI_MENU_CUSTOM_VISIBLE), default)

    # --- Timeline / scene ----------------------------------------------
    def timeline_inout_alpha(self, default: int = 128) -> int:
        val = _i(self._s.value(TIMELINE_INOUT_ALPHA, default), default)
        return max(0, min(255, val))

    def scene_background(self) -> str | None:
        v = self._s.value(UI_STYLE_SCENE_BG)
        return str(v) if v else None

    # --- Shortcuts ------------------------------------------------------
    def shortcut(self, action_key: str) -> str | None:
        v = self._s.value(SHORTCUT_KEY(action_key))
        return str(v) if v else None
