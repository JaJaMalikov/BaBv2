"""Shared defaults for overlay menus and icon keys.

Centralizing these avoids duplicate-code (pylint R0801) across modules.
"""

MAIN_DEFAULT_ORDER = [
    "save",
    "load",
    "scene_size",
    "background",
    "add_light",
    "settings",
    "reset_scene",
    "reset_ui",
    "toggle_library",
    "toggle_inspector",
    "toggle_timeline",
    "toggle_custom",
]

QUICK_DEFAULT_ORDER = [
    "zoom_out",
    "zoom_in",
    "fit",
    "handles",
    "onion",
]

CUSTOM_DEFAULT_ORDER = [
    "save",
    "load",
    "scene_size",
    "background",
    "settings",
    "zoom_out",
    "zoom_in",
    "fit",
    "handles",
    "onion",
]

COMMON_ICON_KEYS = {
    "open_menu",
    "close_menu",
    "close_menu_inv",
    "chevron_left",
    "chevron_right",
    "save",
    "open",
    "scene_size",
    "background",
    "settings",
    "reset_scene",
    "reset_ui",
    "library",
    "inspector",
    "timeline",
    "layers",
    "zoom_out",
    "zoom_in",
    "fit",
    "handles",
    "onion",
    "delete",
    "duplicate",
    "link",
    "link_off",
    "close",
    "objets",
    "puppet",
    "new_file",
    "plus",
    "minus",
    "rotate",
    "custom",
    "add_light",
    # Expanded to centralize commonly used icons across UI (docs/tasks.md §12)
    "play",
    "pause",
    "stop",
    "first",
    "last",
    "repeat",
    "repeat_on",
    "download",
    "upload",
    "warning",
}
