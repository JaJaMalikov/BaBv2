# Settings schema and keys

This document summarizes the settings persisted via QSettings and the UI profile JSON. It reflects the current implementation in ui/ui_profile.py and ui/settings_manager.py.

Namespace: ORG=JaJa, APP=Macronotron

## Theme (ThemeSettings)
- theme.preset: str (dark|light|custom)
- theme.font_family: str
- theme.font_size: int
- theme.accent: str (hex color)

## Icons
- ui/icon_dir: str (optional custom icon directory)
- ui/icon_size: int (default 20)
- ui/icon_color_normal: str (hex)
- ui/icon_color_hover: str (hex)
- ui/icon_color_active: str (hex)
- ui/icon_override/<key>: str (absolute or project-relative path)

## Timeline
- timeline/bg: str (hex)
- timeline/ruler_bg: str (hex)
- timeline/track_bg: str (hex)
- timeline/tick: str (hex)
- timeline/tick_major: str (hex)
- timeline/playhead: str (hex)
- timeline/kf: str (hex)
- timeline/kf_hover: str (hex)
- timeline/inout_alpha: int (0-255)

## Scene
- ui/style/scene_bg: str (hex) or empty

## Overlay menus
- ui/menu/custom/visible: bool
- ui/menu/main/order: list[str]
- ui/menu/quick/order: list[str]
- ui/menu/custom/order: list[str]
- ui/menu/<prefix>/<key>: bool (visibility for each key in order)

Known keys are seeded from:
- ui/menu_defaults.py: MAIN_DEFAULT_ORDER, QUICK_DEFAULT_ORDER, CUSTOM_DEFAULT_ORDER

## Geometries and layout
- geometry/library: QRect serialized by QSettings
- geometry/inspector: QRect
- geometry/view_toolbar: QRect
- geometry/main_toolbar: QRect
- layout/timeline_visible: bool

## Import/export
The UI profile can be exported/imported as JSON via the Settings dialog. The JSON mirrors the UIProfile dataclass (ui/ui_profile.py), including:
- theme, icon settings, timeline colors, menu orders/visibility, overrides, geometry, timeline visibility.

Unknown fields should be ignored gracefully to allow forward-compatible profiles.

## Notes
- Paths in ui/icon_override may be absolute or relative to the repository root; prefer project-relative when possible.
- Color strings are stored as hex (e.g., #AABBCC). Invalid values are ignored and defaults are used.
