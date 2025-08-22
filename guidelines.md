Project-specific development guidelines for BaBv2 (Macronotron)

Audience: Advanced Python/PySide6 developers working on this repository. Focus on details unique to this codebase: headless UI testing, QSettings-based configuration, scene IO/validation, MVC boundaries, and theming/icons.

1. Build and configuration

- Runtime
  - Python: 3.10+ recommended.
  - OS: Linux/macOS/Windows. PySide6 must be installed; on Linux ensure Qt platform plugins (xcb/wayland) are available.
  - Install dependencies: pip install -r requirements.txt
  - Run the app: python macronotron.py
  - Headless environment: tests run with QT_QPA_PLATFORM=offscreen (set by tests/conftest.py). For interactive runs on Linux use xcb or wayland (e.g., export QT_QPA_PLATFORM=xcb) if needed.

- Application settings (QSettings)
  - Organization/App: JaJa / Macronotron. Any persistent UI state is written under this scope (platform-native store or ~/.config/JaJa/Macronotron on Linux).
  - Primary keys consumed by the app (non-exhaustive, but stable):
    - geometry/*: mainwindow, library, inspector, view_toolbar, main_toolbar
    - layout/timeline_visible: bool
    - ui/icon_dir: optional directory overriding assets/icons lookup
    - ui/icon_size: int (default 32)
    - ui/theme: one of light | dark | high contrast | custom
    - ui/theme_file: path to JSON when using custom theme
    - ui/font_family: font family (default Poppins)
    - ui/custom_params/*: custom theme parameters (see ThemeSettings.DEFAULT_CUSTOM_PARAMS)
    - ui/style/scene_bg: optional scene background color/asset
    - ui/menu/{main,quick,custom}/order: list or CSV of action keys
    - ui/menu/{main,quick,custom}/{action_key}: bool visibility flag per action
    - ui/menu/custom/visible: bool
    - ui/icon_override/{name}: file path per icon key (SVG preferred)
    - ui/icon_color_{normal,hover,active}: hex colors used to tint SVG icons
    - timeline/*: bg, ruler_bg, track_bg, tick, tick_major, playhead, kf, kf_hover, inout_alpha
    - shortcuts/*: action key -> QKeySequence string
  - SettingsManager.clear() only removes geometry/layout keys, leaving theme/icon/timeline configuration intact.
  - Type nuances:
    - QSettings may return strings for booleans; code handles values like "true". When writing additional code, normalize via helper patterns in ui/ui_profile.py (_bool).

- UI/theme system
  - ThemeSettings centralizes theme preset and custom parameters; can round-trip to QSettings and JSON in ~/.config/JaJa/Macronotron/theme.json.
  - UIProfile aggregates theme, icon palette, timeline colors, overlay/menu visibility/order, overlay geometries, and icon overrides. Prefer using UIProfile for bulk configuration import/export or for tests.

- Icons
  - Default icons live in assets/icons/*.svg; dynamic coloring is applied by ui/icons.py based on QSettings icon colors.
  - Override search path: ui/icon_dir. Per-icon override: ui/icon_override/{name} (supports .svg and bitmap). Fallback mapping exists (e.g., custom -> layers, settings -> layers).
  - When adding icons, stick to simple path-based SVGs so fill substitution works; or provide a flat bitmap fallback.

- Overlays and docks
  - Panel overlays (Library/Inspector) are created via ui/panels.py and orchestrated by ui/overlay_manager.py. Geometries are persisted in QSettings geometry/*.

2. Testing

- Running tests
  - Standard: pytest -q
  - Headless mode is enforced by tests/conftest.py (QT_QPA_PLATFORM=offscreen) and a module-scoped QApplication fixture (_app). You usually don’t need to manipulate Qt platform env vars in tests.
  - Run a subset: pytest -k name_substring -q

- UI test patterns
  - Avoid blocking dialogs: patch QDialog.exec to non-blocking open as shown in tests/test_ui_introspection.py
    monkeypatch.setattr(QDialog, "exec", lambda self: self.open())
  - Process events when needed: QApplication.processEvents() or QTimer.singleShot(0, ...) to allow the event loop to settle.
  - Don’t rely on actual display; assume offscreen rendering. Avoid pixel assertions; prefer structural checks (widget existence, state flags, geometry ranges).

- File dialogs and IO
  - When testing import/export, bypass QFileDialog by calling ui.scene.scene_io.export_scene(win, path) or import_scene(win, path) directly.
  - Use tmp_path for writing JSONs. The export function ensures a keyframe exists and attempts to snapshot the current frame.

- QSettings side effects
  - Tests run against the real QSettings scope (JaJa/Macronotron). If a test alters global visual settings (theme/icon colors), revert them or run in isolation.
  - Prefer avoiding preset "custom" in tests to prevent JSON writes under ~/.config. If you must exercise custom persistence, monkeypatch Path.home() to a tmp directory.

- Scene model validation
  - core/scene_validation provides validate_settings/objects/keyframes used in serialization. Keep types strict: ints for frame range/fps/size; dict for objects; list[dict] for keyframes with optional int index.

- Adding new tests
  - UI: leverage the _app fixture (or create a local one) to ensure a QApplication exists. Avoid long-lived timers and blocking dialogs. Use monkeypatch to neutralize file IO interactions.
  - Core: test core modules (core/*) without Qt. Aim for pure functions/dataclasses and validate JSON round-trips via SceneModel.to_dict/from_dict.

3. Development practices

- Architecture boundaries (reinforced by ARCHITECTURE.md)
  - core/: pure model & serialization, no Qt.
  - controllers/: orchestration and application of model states to the views; connect signals/slots; no persistent UI state.
  - ui/: widgets and views; emit user-intent signals; no direct modification of the model except via controllers.
  - Use typing.Protocol where necessary to minimize coupling between layers (e.g., window/widget contracts).

- Startup sequence
  - macronotron.py: create_app() ensures a single QApplication and applies stylesheet; main() instantiates ui.main_window.MainWindow and enters the event loop.
  - MainWindow delegates to controllers and helpers:
    - OverlayManager builds/positions overlays.
    - SettingsManager persists/restores geometries and loads shortcuts.
    - AppController.startup_sequence() shows the window, ensures fit, creates a blank scene (via ui.scene.scene_io.create_blank_scene), and wires selection updates.

- Scene IO specifics
  - export_scene writes SceneModel.to_dict() plus a puppets_data map capturing root puppet pose (path, scale, position, rotation, z_offset) based on graphics state.
  - import_scene clears the scene, loads model via SceneModel.from_dict(), re-adds puppets from puppets_data when paths exist, reapplies scale/position/rotation/z-offset, rebuilds object graphics, refreshes timeline UI and inspector, then enforces a visual update via controller.
  - create_blank_scene optionally adds assets/pantins/manu.svg when add_default_puppet=True.

- Settings and shortcuts
  - SettingsManager uses QSettings("JaJa","Macronotron") and only persists/restores non-model UI state. Shortcuts are stored under the shortcuts group and mapped to QAction objects present on MainWindow.
  - Be careful with QSettings value types; normalize booleans and ints before using them (reference ui/ui_profile.py and SettingsManager.load()).

- Styling
  - ui/styles.py builds the application stylesheet based on ThemeSettings/UIProfile. The default light/dark constants provide a baseline; custom themes read from QSettings/JSON.
  - Font family is taken from ui/font_family; default Poppins. Ensure the font is available on target systems or provide fallbacks.

- Icons
  - ui/icons.py applies dynamic tinting to SVGs by substituting fill on <path> tags; keep SVGs simple. Non-SVG bitmaps are supported but lose tint dynamics.
  - When you add new action keys, consider updating fallback_map in ui/icons._create_icon and adding assets.

- Common pitfalls
  - Don’t block the event loop in tests; avoid exec() on dialogs.
  - QSettings may store booleans as strings; normalize before use.
  - Geometry restoration must be applied after widgets exist; when adding new overlays/toolbars, call raise_() as done in SettingsManager.load().
  - Avoid directly mutating view/model across layers; route changes via controllers.

- Linting & style
  - pylint is available. Follow PEP8 with project conventions:
    - signals: snake_case like frame_update_requested/current_frame_changed for new Python-side signals; camelCase is acceptable for Qt-native ones.
    - typing: prefer precise typing, Protocols for view contracts.
    - functions: keep UI code resilient to missing widgets (hasattr checks are common in this codebase).

4. How to extend typical features

- Add a menu action
  - Define the action in the relevant ui/views/*/actions module.
  - Register it in ui/menu_defaults.py (orders/visibility defaults).
  - Ensure OverlayManager.apply_menu_settings() updates views (view.apply_menu_settings_main/quick).
  - Provide an icon in assets/icons and refer to it by action key; update icon overrides via QSettings if needed.

- Add a new overlay/tool panel
  - Extend ui/panels.py to build the overlay and return both overlay and widget; persist geometry under geometry/*.
  - Wire visibility toggles through OverlayManager and connect actions in MainWindow.

- Add a theme variable
  - Add default to ThemeSettings.DEFAULT_CUSTOM_PARAMS and teach ui/styles.py to consume it.
  - Make it editable in settings dialog (ui/settings_dialog.py) and persisted via SettingsManager.

- Add/modify scene serialization
  - Keep core/scene_model.py as the source of truth for data layout; adjust validate_* in core/scene_validation.py as needed.
  - Update ui/scene/scene_io.py to include any extra view-derived fields in puppets_data or similar.

5. Debugging tips

- Use logging at INFO/DEBUG; many modules are defensive and log exceptions with context rather than raising.
- For headless debugging, print widget trees similarly to tests/test_ui_introspection.py to understand visibility/structure.
- When geometry/visibility looks wrong after settings changes, try SettingsManager.clear() to reset persisted layout keys and retest.

Appendix: quick references

- Entrypoint: macronotron.py (create_app, main)
- Main window: ui/main_window.py
- Controllers: controllers/app_controller.py, controllers/*
- Scene model and validation: core/scene_model.py, core/scene_validation.py
- Scene IO: ui/scene/scene_io.py
- Overlays: ui/panels.py, ui/overlay_manager.py
- Icons: ui/icons.py
- Theming & styles: ui/theme_settings.py, ui/styles.py
- UI profile: ui/ui_profile.py
- Tests entry: tests/ (pytest), headless config: tests/conftest.py
