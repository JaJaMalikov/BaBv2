"""Central UI profile: a single source of truth for all visual settings.

Includes theme (colors, fonts), icon palette, timeline colors, overlay/menu
visibility and order, basic overlay geometries, and icon overrides. Provides
safe JSON import/export with defaults and QSettings round‑trip.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging

from PySide6.QtCore import QSettings, QRect

from .theme_settings import ThemeSettings
from .menu_defaults import MAIN_DEFAULT_ORDER, QUICK_DEFAULT_ORDER, CUSTOM_DEFAULT_ORDER


def _bool(v: Any, default: bool = False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "on"}


def _int(v: Any, default: int = 0) -> int:
    """Normalize an int value coming from QSettings.
    Accepts ints or numeric strings; falls back to default on failure.
    """
    if v is None:
        return default
    try:
        if isinstance(v, (int,)):
            return int(v)
        s = str(v).strip()
        # Handle floats that are effectively ints
        if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
            return int(s)
        return int(float(s))
    except Exception:
        return default


def _float(v: Any, default: float = 0.0) -> float:
    """Normalize a float value coming from QSettings.
    Accepts floats or numeric strings; falls back to default on failure.
    """
    if v is None:
        return default
    try:
        if isinstance(v, (float, int)):
            return float(v)
        s = str(v).strip().replace(",", ".")
        return float(s)
    except Exception:
        return default


def _color(v: Any, default: str = "#000000") -> str:
    """Normalize a color string from QSettings.
    Accepts hex colors like #RRGGBB or #RRGGBBAA; returns default on invalid.
    """
    if not v:
        return default
    s = str(v).strip()
    if s.startswith("#") and len(s) in (7, 9):
        try:
            int(s[1:], 16)
            return s
        except Exception:
            return default
    # Pass through known rgba() values without validation
    if s.lower().startswith("rgba("):
        return s
    return default


def _rect_to_tuple(r: Any) -> Optional[Tuple[int, int, int, int]]:
    try:
        if isinstance(r, QRect):
            return (r.x(), r.y(), r.width(), r.height())
    except Exception:
        pass
    return None


def _tuple_to_rect(t: Any) -> Optional[QRect]:
    try:
        x, y, w, h = map(int, list(t))
        return QRect(x, y, w, h)
    except Exception:
        return None


@dataclass
class UIProfile:
    version: int = 1
    theme: ThemeSettings = field(default_factory=ThemeSettings)

    # Icon palette + base icons config
    icon_dir: str | None = None
    icon_size: int = 32
    icon_color_normal: str = "#4A5568"
    icon_color_hover: str = "#E53E3E"
    icon_color_active: str = "#FFFFFF"

    # Timeline palette
    timeline_bg: str = "#1E1E1E"
    timeline_ruler_bg: str = "#2C2C2C"
    timeline_track_bg: str = "#242424"
    timeline_tick: str = "#8A8A8A"
    timeline_tick_major: str = "#E0E0E0"
    timeline_playhead: str = "#65B0FF"
    timeline_kf: str = "#FFC107"
    timeline_kf_hover: str = "#FFE082"
    timeline_inout_alpha: int = 30

    # Scene visuals
    scene_bg: str | None = None

    # Overlay/menu configuration
    custom_overlay_visible: bool = False
    menu_main_order: List[str] = field(default_factory=lambda: list(MAIN_DEFAULT_ORDER))
    menu_main_vis: Dict[str, bool] = field(default_factory=dict)
    menu_quick_order: List[str] = field(
        default_factory=lambda: list(QUICK_DEFAULT_ORDER)
    )
    menu_quick_vis: Dict[str, bool] = field(default_factory=dict)
    menu_custom_order: List[str] = field(
        default_factory=lambda: list(CUSTOM_DEFAULT_ORDER)
    )
    menu_custom_vis: Dict[str, bool] = field(default_factory=dict)

    # Icon overrides: key -> filepath
    icon_overrides: Dict[str, str] = field(default_factory=dict)

    # Basic overlay geometries (optional): (x,y,w,h)
    geom_library: Optional[Tuple[int, int, int, int]] = None
    geom_inspector: Optional[Tuple[int, int, int, int]] = None
    geom_view_toolbar: Optional[Tuple[int, int, int, int]] = None
    geom_main_toolbar: Optional[Tuple[int, int, int, int]] = None
    timeline_visible: bool = True

    ORG: str = "JaJa"
    APP: str = "Macronotron"

    @classmethod
    def default_dark(cls) -> "UIProfile":
        p = cls()
        p.theme.preset = "dark"
        p.theme.font_family = "Poppins"
        return p

    @classmethod
    def from_qsettings(cls, s: Optional[QSettings] = None) -> "UIProfile":
        s = s or QSettings(cls.ORG, cls.APP)
        p = cls()
        p.theme = ThemeSettings.from_qsettings(s)

        # Icon base
        from ui.settings_keys import (
            UI_ICON_DIR,
            UI_ICON_SIZE,
            UI_ICON_COLOR_NORMAL,
            UI_ICON_COLOR_HOVER,
            UI_ICON_COLOR_ACTIVE,
        )
        p.icon_dir = s.value(UI_ICON_DIR) or None
        try:
            p.icon_size = int(s.value(UI_ICON_SIZE, p.icon_size))
        except Exception:
            pass
        p.icon_color_normal = str(
            s.value(UI_ICON_COLOR_NORMAL) or p.icon_color_normal
        )
        p.icon_color_hover = str(s.value(UI_ICON_COLOR_HOVER) or p.icon_color_hover)
        p.icon_color_active = str(
            s.value(UI_ICON_COLOR_ACTIVE) or p.icon_color_active
        )

        # Timeline (validated)
        def _get_col(key: str, current: str) -> str:
            from ui.settings_keys import (
                TIMELINE_BG,
                TIMELINE_RULER_BG,
                TIMELINE_TRACK_BG,
                TIMELINE_TICK,
                TIMELINE_TICK_MAJOR,
                TIMELINE_PLAYHEAD,
                TIMELINE_KF,
                TIMELINE_KF_HOVER,
            )
            key_map = {
                "bg": TIMELINE_BG,
                "ruler_bg": TIMELINE_RULER_BG,
                "track_bg": TIMELINE_TRACK_BG,
                "tick": TIMELINE_TICK,
                "tick_major": TIMELINE_TICK_MAJOR,
                "playhead": TIMELINE_PLAYHEAD,
                "kf": TIMELINE_KF,
                "kf_hover": TIMELINE_KF_HOVER,
            }
            raw = s.value(key_map.get(key, f"timeline/{key}"))
            if raw is None or raw == "":
                return current
            val = _color(raw, current)
            if str(raw).strip() != val:
                logging.warning(
                    "timeline: invalid color for %s=%r; using default %s",
                    key,
                    raw,
                    current,
                )
            return val

        p.timeline_bg = _get_col("bg", p.timeline_bg)
        p.timeline_ruler_bg = _get_col("ruler_bg", p.timeline_ruler_bg)
        p.timeline_track_bg = _get_col("track_bg", p.timeline_track_bg)
        p.timeline_tick = _get_col("tick", p.timeline_tick)
        p.timeline_tick_major = _get_col("tick_major", p.timeline_tick_major)
        p.timeline_playhead = _get_col("playhead", p.timeline_playhead)
        p.timeline_kf = _get_col("kf", p.timeline_kf)
        p.timeline_kf_hover = _get_col("kf_hover", p.timeline_kf_hover)

        from ui.settings_keys import (
            TIMELINE_INOUT_ALPHA,
            UI_STYLE_SCENE_BG,
            UI_MENU_CUSTOM_VISIBLE,
            UI_MENU_ORDER,
            UI_MENU_VIS,
            UI_ICON_OVERRIDE,
            GEOMETRY_LIBRARY,
            GEOMETRY_INSPECTOR,
            GEOMETRY_VIEW_TOOLBAR,
            GEOMETRY_MAIN_TOOLBAR,
            LAYOUT_TIMELINE_VISIBLE,
        )
        raw_alpha = s.value(TIMELINE_INOUT_ALPHA, p.timeline_inout_alpha)
        a = _int(raw_alpha, p.timeline_inout_alpha)
        clamped = max(0, min(255, a))
        if clamped != a:
            logging.warning(
                "timeline: clamped inout_alpha from %s to %s (range 0..255)", a, clamped
            )
        p.timeline_inout_alpha = clamped

        # Scene bg
        p.scene_bg = s.value(UI_STYLE_SCENE_BG) or None

        # Overlay/menu
        p.custom_overlay_visible = _bool(s.value(UI_MENU_CUSTOM_VISIBLE), False)

        def get_order_vis(
            prefix: str, default_order: List[str]
        ) -> Tuple[List[str], Dict[str, bool]]:
            order = s.value(UI_MENU_ORDER(prefix)) or list(default_order)
            if isinstance(order, str):
                order = [k for k in order.split(",") if k]
            vis: Dict[str, bool] = {}
            for k in order:
                vis[k] = _bool(s.value(UI_MENU_VIS(prefix, k)), True)
            return list(order), vis

        p.menu_main_order, p.menu_main_vis = get_order_vis("main", p.menu_main_order)
        p.menu_quick_order, p.menu_quick_vis = get_order_vis(
            "quick", p.menu_quick_order
        )
        p.menu_custom_order, p.menu_custom_vis = get_order_vis(
            "custom", p.menu_custom_order
        )

        # Icon overrides (shallow scan of known keys)
        # Persist what we find in the overlay specs keys to keep JSON small.
        keys = set(p.menu_main_order + p.menu_quick_order + p.menu_custom_order)
        overrides: Dict[str, str] = {}
        for k in keys:
            v = s.value(UI_ICON_OVERRIDE(k))
            if v:
                overrides[k] = str(v)
        p.icon_overrides = overrides

        # Geometries
        p.geom_library = _rect_to_tuple(s.value(GEOMETRY_LIBRARY)) or p.geom_library
        p.geom_inspector = (
            _rect_to_tuple(s.value(GEOMETRY_INSPECTOR)) or p.geom_inspector
        )
        p.geom_view_toolbar = (
            _rect_to_tuple(s.value(GEOMETRY_VIEW_TOOLBAR)) or p.geom_view_toolbar
        )
        p.geom_main_toolbar = (
            _rect_to_tuple(s.value(GEOMETRY_MAIN_TOOLBAR)) or p.geom_main_toolbar
        )
        p.timeline_visible = _bool(s.value(LAYOUT_TIMELINE_VISIBLE), True)
        return p

    def apply_to_qsettings(self, s: Optional[QSettings] = None) -> None:
        s = s or QSettings(self.ORG, self.APP)
        # Theme first
        self.theme.to_qsettings(s)
        # Icon base
        from ui.settings_keys import (
            UI_ICON_DIR,
            UI_ICON_SIZE,
            UI_ICON_COLOR_NORMAL,
            UI_ICON_COLOR_HOVER,
            UI_ICON_COLOR_ACTIVE,
            TIMELINE_BG,
            TIMELINE_RULER_BG,
            TIMELINE_TRACK_BG,
            TIMELINE_TICK,
            TIMELINE_TICK_MAJOR,
            TIMELINE_PLAYHEAD,
            TIMELINE_KF,
            TIMELINE_KF_HOVER,
            TIMELINE_INOUT_ALPHA,
            UI_STYLE_SCENE_BG,
            UI_MENU_CUSTOM_VISIBLE,
            UI_MENU_ORDER,
            UI_MENU_VIS,
            UI_ICON_OVERRIDE,
            GEOMETRY_LIBRARY,
            GEOMETRY_INSPECTOR,
            GEOMETRY_VIEW_TOOLBAR,
            GEOMETRY_MAIN_TOOLBAR,
            LAYOUT_TIMELINE_VISIBLE,
        )
        s.setValue(UI_ICON_DIR, self.icon_dir or "")
        s.setValue(UI_ICON_SIZE, int(self.icon_size))
        s.setValue(UI_ICON_COLOR_NORMAL, self.icon_color_normal)
        s.setValue(UI_ICON_COLOR_HOVER, self.icon_color_hover)
        s.setValue(UI_ICON_COLOR_ACTIVE, self.icon_color_active)
        # Timeline
        s.setValue(TIMELINE_BG, self.timeline_bg)
        s.setValue(TIMELINE_RULER_BG, self.timeline_ruler_bg)
        s.setValue(TIMELINE_TRACK_BG, self.timeline_track_bg)
        s.setValue(TIMELINE_TICK, self.timeline_tick)
        s.setValue(TIMELINE_TICK_MAJOR, self.timeline_tick_major)
        s.setValue(TIMELINE_PLAYHEAD, self.timeline_playhead)
        s.setValue(TIMELINE_KF, self.timeline_kf)
        s.setValue(TIMELINE_KF_HOVER, self.timeline_kf_hover)
        s.setValue(TIMELINE_INOUT_ALPHA, int(self.timeline_inout_alpha))
        # Scene
        s.setValue(UI_STYLE_SCENE_BG, self.scene_bg or "")
        # Menus
        s.setValue(UI_MENU_CUSTOM_VISIBLE, bool(self.custom_overlay_visible))

        def set_order_vis(prefix: str, order: List[str], vis: Dict[str, bool]) -> None:
            s.setValue(UI_MENU_ORDER(prefix), order)
            for k in order:
                s.setValue(UI_MENU_VIS(prefix, k), bool(vis.get(k, True)))

        set_order_vis("main", self.menu_main_order, self.menu_main_vis)
        set_order_vis("quick", self.menu_quick_order, self.menu_quick_vis)
        set_order_vis("custom", self.menu_custom_order, self.menu_custom_vis)
        # Overrides
        for k, v in (self.icon_overrides or {}).items():
            s.setValue(UI_ICON_OVERRIDE(k), v)
        # Geometries
        if self.geom_library:
            r = _tuple_to_rect(self.geom_library)
            if r:
                s.setValue(GEOMETRY_LIBRARY, r)
        if self.geom_inspector:
            r = _tuple_to_rect(self.geom_inspector)
            if r:
                s.setValue(GEOMETRY_INSPECTOR, r)
        if self.geom_view_toolbar:
            r = _tuple_to_rect(self.geom_view_toolbar)
            if r:
                s.setValue(GEOMETRY_VIEW_TOOLBAR, r)
        if self.geom_main_toolbar:
            r = _tuple_to_rect(self.geom_main_toolbar)
            if r:
                s.setValue(GEOMETRY_MAIN_TOOLBAR, r)
        s.setValue(LAYOUT_TIMELINE_VISIBLE, bool(self.timeline_visible))

    # JSON I/O -----------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # ThemeSettings is dataclass-safe already
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UIProfile":
        p = cls.default_dark() if not isinstance(data, dict) else cls()
        try:
            p.version = int(data.get("version", p.version))
        except Exception:
            p.version = 1
        # Theme
        tdata = data.get("theme")
        if isinstance(tdata, dict):
            t = ThemeSettings()
            t.preset = str(tdata.get("preset", t.preset)).lower()
            t.font_family = str(tdata.get("font_family", t.font_family))
            if isinstance(tdata.get("custom_params"), dict):
                t.custom_params.update(tdata["custom_params"])  # type: ignore[index]
            p.theme = t
        # Shallow scalar fields
        for k in [
            "icon_dir",
            "icon_size",
            "icon_color_normal",
            "icon_color_hover",
            "icon_color_active",
            "timeline_bg",
            "timeline_ruler_bg",
            "timeline_track_bg",
            "timeline_tick",
            "timeline_tick_major",
            "timeline_playhead",
            "timeline_kf",
            "timeline_kf_hover",
            "timeline_inout_alpha",
            "scene_bg",
            "custom_overlay_visible",
            "timeline_visible",
        ]:
            if k in data:
                setattr(p, k, data[k])
        # Lists/dicts
        for k in [
            "menu_main_order",
            "menu_quick_order",
            "menu_custom_order",
        ]:
            if isinstance(data.get(k), list):
                setattr(p, k, list(data[k]))
        for k in [
            "menu_main_vis",
            "menu_quick_vis",
            "menu_custom_vis",
            "icon_overrides",
        ]:
            if isinstance(data.get(k), dict):
                setattr(p, k, dict(data[k]))
        # Geoms
        for k in [
            "geom_library",
            "geom_inspector",
            "geom_view_toolbar",
            "geom_main_toolbar",
        ]:
            if k in data and isinstance(data[k], (list, tuple)):
                setattr(p, k, tuple(map(int, data[k])))
        return p

    def export_json(self, path: str) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        from json import dumps

        p.write_text(dumps(self.to_dict(), indent=2), encoding="utf-8")
        return str(p)

    @classmethod
    def import_json(cls, path: str) -> "UIProfile":
        try:
            from json import load

            with open(path, "r", encoding="utf-8") as f:
                data = load(f)
            return cls.from_dict(data if isinstance(data, dict) else {})
        except Exception:
            # Fallback to default dark
            return cls.default_dark()
