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


def _rect_to_tuple(r: Any) -> Optional[Tuple[int, int, int, int]]:
    try:
        if isinstance(r, QRect):
            return (r.x(), r.y(), r.width(), r.height())
    except (AttributeError, TypeError):
        pass
    return None


def _tuple_to_rect(t: Any) -> Optional[QRect]:
    try:
        x, y, w, h = map(int, list(t))
        return QRect(x, y, w, h)
    except (TypeError, ValueError):
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
    menu_quick_order: List[str] = field(default_factory=lambda: list(QUICK_DEFAULT_ORDER))
    menu_quick_vis: Dict[str, bool] = field(default_factory=dict)
    menu_custom_order: List[str] = field(default_factory=lambda: list(CUSTOM_DEFAULT_ORDER))
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
        p.icon_dir = s.value("ui/icon_dir") or None
        try:
            p.icon_size = int(s.value("ui/icon_size", p.icon_size))
        except (TypeError, ValueError):
            pass
        p.icon_color_normal = str(s.value("ui/icon_color_normal") or p.icon_color_normal)
        p.icon_color_hover = str(s.value("ui/icon_color_hover") or p.icon_color_hover)
        p.icon_color_active = str(s.value("ui/icon_color_active") or p.icon_color_active)

        # Timeline
        p.timeline_bg = str(s.value("timeline/bg") or p.timeline_bg)
        p.timeline_ruler_bg = str(s.value("timeline/ruler_bg") or p.timeline_ruler_bg)
        p.timeline_track_bg = str(s.value("timeline/track_bg") or p.timeline_track_bg)
        p.timeline_tick = str(s.value("timeline/tick") or p.timeline_tick)
        p.timeline_tick_major = str(s.value("timeline/tick_major") or p.timeline_tick_major)
        p.timeline_playhead = str(s.value("timeline/playhead") or p.timeline_playhead)
        p.timeline_kf = str(s.value("timeline/kf") or p.timeline_kf)
        p.timeline_kf_hover = str(s.value("timeline/kf_hover") or p.timeline_kf_hover)
        try:
            p.timeline_inout_alpha = int(s.value("timeline/inout_alpha", p.timeline_inout_alpha))
        except Exception:
            pass

        # Scene bg
        p.scene_bg = s.value("ui/style/scene_bg") or None

        # Overlay/menu
        p.custom_overlay_visible = _bool(s.value("ui/menu/custom/visible"), False)

        def get_order_vis(
            prefix: str, default_order: List[str]
        ) -> Tuple[List[str], Dict[str, bool]]:
            order = s.value(f"ui/menu/{prefix}/order") or list(default_order)
            if isinstance(order, str):
                order = [k for k in order.split(",") if k]
            vis: Dict[str, bool] = {}
            for k in order:
                vis[k] = _bool(s.value(f"ui/menu/{prefix}/{k}"), True)
            return list(order), vis

        p.menu_main_order, p.menu_main_vis = get_order_vis("main", p.menu_main_order)
        p.menu_quick_order, p.menu_quick_vis = get_order_vis("quick", p.menu_quick_order)
        p.menu_custom_order, p.menu_custom_vis = get_order_vis("custom", p.menu_custom_order)

        # Icon overrides (shallow scan of known keys)
        # Persist what we find in the overlay specs keys to keep JSON small.
        keys = set(p.menu_main_order + p.menu_quick_order + p.menu_custom_order)
        overrides: Dict[str, str] = {}
        for k in keys:
            v = s.value(f"ui/icon_override/{k}")
            if v:
                overrides[k] = str(v)
        p.icon_overrides = overrides

        # Geometries
        p.geom_library = _rect_to_tuple(s.value("geometry/library")) or p.geom_library
        p.geom_inspector = _rect_to_tuple(s.value("geometry/inspector")) or p.geom_inspector
        p.geom_view_toolbar = (
            _rect_to_tuple(s.value("geometry/view_toolbar")) or p.geom_view_toolbar
        )
        p.geom_main_toolbar = (
            _rect_to_tuple(s.value("geometry/main_toolbar")) or p.geom_main_toolbar
        )
        p.timeline_visible = _bool(s.value("layout/timeline_visible"), True)
        return p

    def apply_to_qsettings(self, s: Optional[QSettings] = None) -> None:
        s = s or QSettings(self.ORG, self.APP)
        # Theme first
        self.theme.to_qsettings(s)
        # Icon base
        s.setValue("ui/icon_dir", self.icon_dir or "")
        s.setValue("ui/icon_size", int(self.icon_size))
        s.setValue("ui/icon_color_normal", self.icon_color_normal)
        s.setValue("ui/icon_color_hover", self.icon_color_hover)
        s.setValue("ui/icon_color_active", self.icon_color_active)
        # Timeline
        s.setValue("timeline/bg", self.timeline_bg)
        s.setValue("timeline/ruler_bg", self.timeline_ruler_bg)
        s.setValue("timeline/track_bg", self.timeline_track_bg)
        s.setValue("timeline/tick", self.timeline_tick)
        s.setValue("timeline/tick_major", self.timeline_tick_major)
        s.setValue("timeline/playhead", self.timeline_playhead)
        s.setValue("timeline/kf", self.timeline_kf)
        s.setValue("timeline/kf_hover", self.timeline_kf_hover)
        s.setValue("timeline/inout_alpha", int(self.timeline_inout_alpha))
        # Scene
        s.setValue("ui/style/scene_bg", self.scene_bg or "")
        # Menus
        s.setValue("ui/menu/custom/visible", bool(self.custom_overlay_visible))

        def set_order_vis(prefix: str, order: List[str], vis: Dict[str, bool]) -> None:
            s.setValue(f"ui/menu/{prefix}/order", order)
            for k in order:
                s.setValue(f"ui/menu/{prefix}/{k}", bool(vis.get(k, True)))

        set_order_vis("main", self.menu_main_order, self.menu_main_vis)
        set_order_vis("quick", self.menu_quick_order, self.menu_quick_vis)
        set_order_vis("custom", self.menu_custom_order, self.menu_custom_vis)
        # Overrides
        for k, v in (self.icon_overrides or {}).items():
            s.setValue(f"ui/icon_override/{k}", v)
        # Geometries
        if self.geom_library:
            r = _tuple_to_rect(self.geom_library)
            if r:
                s.setValue("geometry/library", r)
        if self.geom_inspector:
            r = _tuple_to_rect(self.geom_inspector)
            if r:
                s.setValue("geometry/inspector", r)
        if self.geom_view_toolbar:
            r = _tuple_to_rect(self.geom_view_toolbar)
            if r:
                s.setValue("geometry/view_toolbar", r)
        if self.geom_main_toolbar:
            r = _tuple_to_rect(self.geom_main_toolbar)
            if r:
                s.setValue("geometry/main_toolbar", r)
        s.setValue("layout/timeline_visible", bool(self.timeline_visible))

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
        except (TypeError, ValueError):
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
        except (OSError, ValueError, TypeError) as err:
            logging.warning("Failed to import UIProfile JSON from %s: %s", path, err)
            # Fallback to default dark
            return cls.default_dark()
