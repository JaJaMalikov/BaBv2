"""Theme settings model and persistence helpers.

Encapsulates theme preset, custom style parameters, and font settings.
Centralizes QSettings keys and JSON import/export to reduce duplication
across the UI settings code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QSettings


@dataclass(frozen=True)
class ThemeParam:
    """Definition of a single customizable theme value."""

    key: str
    widget: str
    default: Any
    fallback: Optional[str] = None
    percent: bool = False  # Indicates a spin box storing percent (0-100)


# Order matters for fallback resolution (base colors before dependants)
THEME_PARAMS: List[ThemeParam] = [
    ThemeParam("bg_color", "bg_edit", "#E2E8F0"),
    ThemeParam("text_color", "text_edit", "#1A202C"),
    ThemeParam("accent_color", "accent_edit", "#E53E3E"),
    ThemeParam("hover_color", "hover_edit", "#E3E6FD"),
    ThemeParam("panel_bg", "panel_edit", "#F7F8FC"),
    ThemeParam("panel_opacity", "opacity_spin", 0.9, percent=True),
    ThemeParam("panel_border", "border_edit", "#D0D5DD"),
    ThemeParam("header_bg", "header_bg_edit", ""),
    ThemeParam("header_text", "header_text_edit", "#1A202C", fallback="text_color"),
    ThemeParam(
        "header_border", "header_border_edit", "#D0D5DD", fallback="panel_border"
    ),
    ThemeParam("group_title_color", "group_edit", "#2D3748"),
    ThemeParam("tooltip_bg", "tooltip_bg_edit", "#F7F8FC", fallback="panel_bg"),
    ThemeParam("tooltip_text", "tooltip_text_edit", "#1A202C", fallback="text_color"),
    ThemeParam("tooltip_border", "border_edit", "#D0D5DD", fallback="panel_border"),
    ThemeParam("radius", "radius_spin", 12),
    ThemeParam("font_size", "font_spin", 10),
    ThemeParam("font_family", "font_family_edit", "Poppins"),
    # Inputs/lists/checkboxes exposed
    ThemeParam("input_bg", "input_bg_edit", "#EDF2F7"),
    ThemeParam("input_border", "input_border_edit", "#CBD5E0"),
    ThemeParam("input_text", "input_text_edit", "#1A202C", fallback="text_color"),
    ThemeParam("input_focus_bg", "input_focus_bg_edit", "#FFFFFF"),
    ThemeParam(
        "input_focus_border",
        "input_focus_border_edit",
        "#E53E3E",
        fallback="accent_color",
    ),
    ThemeParam("list_hover_bg", "list_hover_edit", "#E2E8F0"),
    ThemeParam(
        "list_selected_bg", "list_sel_bg_edit", "#E53E3E", fallback="accent_color"
    ),
    ThemeParam("list_selected_text", "list_sel_text_edit", "#FFFFFF"),
    ThemeParam("checkbox_unchecked_bg", "cb_un_bg_edit", "#EDF2F7"),
    ThemeParam("checkbox_unchecked_border", "cb_un_border_edit", "#A0AEC0"),
    ThemeParam(
        "checkbox_checked_bg", "cb_ch_bg_edit", "#E53E3E", fallback="accent_color"
    ),
    ThemeParam("checkbox_checked_border", "cb_ch_border_edit", "#C53030"),
    ThemeParam("checkbox_checked_hover", "cb_ch_hover_edit", "#F56565"),
]


DEFAULT_CUSTOM_PARAMS: Dict[str, Any] = {p.key: p.default for p in THEME_PARAMS}


@dataclass
class ThemeSettings:
    """Serializable theme and font settings with helpers for persistence."""

    preset: str = "dark"  # "light" | "dark" | "high contrast" | "custom"
    font_family: str = "Poppins"
    custom_params: Dict[str, Any] = field(
        default_factory=lambda: dict(DEFAULT_CUSTOM_PARAMS)
    )
    theme_file: Optional[str] = None

    ORG: str = "JaJa"
    APP: str = "Macronotron"

    @staticmethod
    def _is_hex_color(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        v = value.strip()
        if not v.startswith("#"):
            return False
        n = len(v)
        if n not in (7, 9):
            return False
        try:
            int(v[1:], 16)
            return True
        except Exception:
            return False

    @classmethod
    def _sanitize_custom_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return a sanitized copy of custom theme params.

        Mirrors ui.styles.sanitize_custom_params to avoid circular import,
        ensuring sanitation even when styles are not yet applied.
        """
        sanitized: Dict[str, Any] = dict(DEFAULT_CUSTOM_PARAMS)
        sanitized.update(
            {k: v for k, v in params.items() if k in DEFAULT_CUSTOM_PARAMS}
        )

        # Validate colors
        for k, dv in DEFAULT_CUSTOM_PARAMS.items():
            if isinstance(dv, str) and dv.startswith("#"):
                v = sanitized.get(k)
                if not cls._is_hex_color(v):
                    sanitized[k] = dv
        # Numeric sanitization
        try:
            op = float(sanitized.get("panel_opacity", 0.9))
        except (TypeError, ValueError):
            op = 0.9
        sanitized["panel_opacity"] = max(0.0, min(1.0, op))

        for key in ("radius", "font_size"):
            try:
                sanitized[key] = int(sanitized.get(key, DEFAULT_CUSTOM_PARAMS[key]))
            except (TypeError, ValueError):
                sanitized[key] = int(DEFAULT_CUSTOM_PARAMS[key])

        # Basic string coercions
        for key in ("font_family", "header_bg", "tooltip_border"):
            v = sanitized.get(key)
            if v is None:
                sanitized[key] = DEFAULT_CUSTOM_PARAMS.get(key, "")
            else:
                sanitized[key] = str(v)

        return sanitized

    @classmethod
    def from_qsettings(cls, s: Optional[QSettings] = None) -> "ThemeSettings":
        """Load theme settings from QSettings, falling back to defaults."""
        s = s or QSettings(cls.ORG, cls.APP)
        from ui.settings_keys import UI_THEME, UI_FONT_FAMILY, UI_THEME_FILE

        preset = str(s.value(UI_THEME, "light")).lower()
        font_family = str(s.value(UI_FONT_FAMILY) or "Poppins")
        theme_file = s.value(UI_THEME_FILE)
        custom_params: Dict[str, Any] = dict(DEFAULT_CUSTOM_PARAMS)

        if preset == "custom":
            # Prefer JSON file contents if available, otherwise QSettings group
            try:
                from json import load

                if theme_file:
                    p = Path(str(theme_file))
                else:
                    p = Path.home() / ".config/JaJa/Macronotron/theme.json"
                if p.exists():
                    with p.open("r", encoding="utf-8") as f:
                        data = load(f)
                        if isinstance(data, dict):
                            custom_params.update(data)
            except Exception:
                # Fallback to QSettings copy
                pass
            s.beginGroup("ui/custom_params")
            try:
                for k, dv in DEFAULT_CUSTOM_PARAMS.items():
                    v = s.value(k)
                    if v is not None and v != "":
                        custom_params[k] = v
            finally:
                s.endGroup()
            # Ensure font_family mirrors top-level value if not explicitly set
            custom_params.setdefault("font_family", font_family)
            # Sanitize early to enforce safe values everywhere (Task 7)
            custom_params = cls._sanitize_custom_params(custom_params)

        return cls(
            preset=preset,
            font_family=font_family,
            custom_params=custom_params,
            theme_file=str(theme_file) if theme_file else None,
        )

    def to_qsettings(self, s: Optional[QSettings] = None) -> None:
        """Persist current theme settings to QSettings (and JSON for custom)."""
        s = s or QSettings(self.ORG, self.APP)
        s.setValue("ui/theme", self.preset)
        s.setValue("ui/font_family", self.font_family or "Poppins")
        if self.preset == "custom":
            # Keep a JSON copy for resilience
            p = (
                Path(self.theme_file)
                if self.theme_file
                else Path.home() / ".config/JaJa/Macronotron/theme.json"
            )
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                from json import dumps

                p.write_text(dumps(self.custom_params, indent=2), encoding="utf-8")
                s.setValue("ui/theme_file", str(p))
            except Exception:
                # Non-fatal; QSettings copy remains
                pass
            s.beginGroup("ui/custom_params")
            try:
                for k, v in self.custom_params.items():
                    s.setValue(k, v)
            finally:
                s.endGroup()

    @classmethod
    def from_json(cls, path: str) -> "ThemeSettings":
        """Load a ThemeSettings from a JSON file path."""
        p = Path(path)
        data: Dict[str, Any] = {}
        if p.exists():
            from json import load

            with p.open("r", encoding="utf-8") as f:
                raw = load(f)
            if isinstance(raw, dict):
                data = raw
        # Assume custom when loading from file
        ts = cls(preset="custom")
        ts.custom_params.update(
            {k: v for k, v in data.items() if k in DEFAULT_CUSTOM_PARAMS}
        )
        # Sanitize early (Task 7)
        ts.custom_params = cls._sanitize_custom_params(ts.custom_params)
        ts.theme_file = str(p)
        ts.font_family = str(data.get("font_family", ts.font_family))
        return ts

    def to_json(self, path: Optional[str] = None) -> str:
        """Write current custom params to JSON; return path used."""
        if path is None:
            path = self.theme_file or str(
                Path.home() / ".config/JaJa/Macronotron/theme.json"
            )
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        from json import dumps

        p.write_text(dumps(self.custom_params, indent=2), encoding="utf-8")
        self.theme_file = str(p)
        return str(p)
