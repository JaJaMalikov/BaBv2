"""Profil UI centralisé : source de vérité unique pour les réglages visuels.

Regroupe thème, icônes, couleurs de timeline, visibilité des menus et
géométries de base. La persistance s'effectue uniquement via un fichier JSON,
sans recours à ``QSettings``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QRect

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
    geom_mainwindow: Optional[Tuple[int, int, int, int]] = None
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
            "geom_mainwindow",
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
