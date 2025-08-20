# BaBv2 Improvement Tasks (Strict MVC + Code Quality)

This document lists actionable, logically ordered tasks to evolve the codebase toward a stricter MVC architecture and improved code quality. Each task is specific, testable, and references the current modules where applicable.

1. [x] Establish architecture boundaries and conventions
   - [x] Add docs/architecture.md describing layer responsibilities (core/, controllers/, ui/), allowed dependencies, and anti-patterns (e.g., UI touching core models directly, controllers importing PySide).
   - [x] Define a dependency rule: core -> controllers -> ui (one-way). No UI imports in controllers; no PySide in core.
   - [x] Document adapter patterns (view adapters, presenters) for Qt widgets to interact with controllers without leaking Qt into core.

2. [x] Introduce a Controller API for view-facing operations (facade)
   - [x] Create a SceneFacade in controllers/ (or extend controllers/scene_service.py) exposing safe methods for UI (select, transform, z-order, attach/detach, duplicate, delete) without exposing raw models/graphics.
   - [x] Replace direct access to main_window.scene_model and object_manager in UI with calls to the facade.
   - [x] Provide minimal dataclasses/DTOs for UI to read state (e.g., SelectedItemInfo, PuppetInfo) without exposing mutable model objects.

3. [x] Refactor InspectorWidget to respect MVC boundaries
   - [x] ui/views/inspector/inspector_widget.py: remove direct reads/writes to scene_model and QGraphicsItems; call controller/facade methods instead.
   - [x] Move transformation logic (scale/rotation/z) into controller methods (set_object_scale, set_object_rotation, set_object_z, set_puppet_rotation, set_puppet_z_offset, scale_puppet by ratio) and have the controller update both model and visuals.
   - [x] Replace _refresh_attach_* to query controller for puppet/member lists; avoid reading model dicts directly.
   - [x] Replace selection highlighting (selectedItems, setSelected) with a selection service in controllers (or via facade) that updates UI selection through signals/adapters.
   - [x] Add unit tests covering inspector-controller interactions (no direct model access in UI) using mocks for facade.

4. [x] Selection synchronization and event signaling
   - [x] Create a lightweight event bus or use Qt signals in a dedicated adapter layer (ui/selection_sync.py can be extended) to broadcast selection changes and frame sync events.
   - [x] Ensure controllers emit domain events (pure Python callbacks or Qt signal adapters) instead of UI polling models.
   - [x] Update UI views to subscribe to these events to refresh state (e.g., InspectorWidget.refresh()).

5. [x] Consolidate settings management (remove duplication, enforce purity)
   - [x] Adopt controllers/settings_service.py (pure dataclass-based) as the single source of truth for persistence.
   - [x] Keep controllers/settings_presenter.py as the UI bridge for onion and future tabs.
   - [x] Shrink ui/settings_manager.py: delegate JSON import/export and default resolution to SettingsService; limit it to dialog assembly and QSettings migration only.
   - [x] Replace hard-coded QSettings key strings with SettingsService.key() helper; add tests to prevent regressions.
   - [x] Add round-trip tests for SettingsService (save/load JSON) and dialog mapping tests via SettingsPresenter.

6. [x] Clarify SceneView responsibilities and decouple from MainWindow
   - [x] ui/scene/scene_view.py: stop calling win._update_zoom_status() directly; introduce a callback or a controller method (e.g., scene_facade.on_zoom_changed) invoked by SceneView.
   - [x] Replace direct win.view.scale() calls with a view adapter exposing scale and status update methods, injected into SceneView.
   - [x] Add tests for SceneView behavior via the adapter mock (no MainWindow dependency).

7. [x] Normalize scene operations across UI modules
   - [x] ui/scene/library_ops.py: replace direct calls to win.inspector_widget.refresh() with event emission (selection or model-changed event) handled by Inspector.
   - [x] Route object/puppet creation via controllers (ObjectController/PuppetOps) and ensure controllers apply both model and visuals consistently.
   - [x] Ensure background changes go only through controllers/scene_service.py, not directly to UI.

8. [x] Reduce direct model/graphics exposure in UI
   - [x] Audit ui/ for any attribute access like main_window.scene_model, object_manager.graphics_items; replace with controller/facade queries and commands.
   - [x] Introduce minimal read-only view models (snapshots) for lists shown in UI (objects, puppets, attachments) instead of handing dicts.

9. [x] Improve validation and error handling at controller boundaries
   - [x] Use core/scene_validation.py in controllers prior to mutating model state; convert errors to user-facing messages via UI adapters.
   - [x] Standardize logging calls (core/logging_config.py) and reduce bare excepts. Prefer logging.exception for unexpected errors.
   - [x] Add explicit return values or exceptions for controller operations; write tests for edge cases (invalid names, missing puppets/members, negative scales).

10. [x] Strengthen type hints and protocols across layers
  - [x] Add Protocols for view adapters (e.g., object selection adapter, zoom status adapter) to decouple controllers from Qt.
  - [x] Complete type hints in controllers and core to enable mypy-like checking (even if mypy is not in CI yet).
  - [x] Add simple TypedDicts or dataclasses for payloads (e.g., ui/scene/library_ops.py already uses LibraryPayload; extend pattern elsewhere).

11. [x] Untangle settings UI composition and persistence
   - [x] ui/settings_dialog.py: move logic manipulating onion controls into SettingsPresenter helpers.
   - [x] ui/settings_manager.py: extract dialog construction/private helpers into smaller functions; remove long nested functions to improve readability and testability.
   - [x] Write focused tests for settings dialog mapping using the _app fixture.

12. [x] Standardize menu/defaults and icon usage
   - [x] Expand ui/menu_defaults.py to include any remaining duplicated icon keys/order lists found elsewhere; refactor imports to use it everywhere.
   - [x] Add a small validation test ensuring all keys in menu defaults exist in assets/icons/ to avoid runtime missing icons.

13. [x] Core purity audit
   - [x] Ensure no PySide6 imports in core/ modules; convert any accidental imports to protocols or move to ui/.
   - [x] Verify serialization code in core/scene_model.py and core/svg_loader.py has no UI dependencies.
   - [x] Add round-trip tests (already present in tests/) for any newly exposed fields.

14. [x] Controller/service API completeness and consistency
   - [x] controllers/scene_service.py: ensure it exposes background size updates, model queries, and validation entry points used by UI.
   - [x] controllers/object_controller.py: centralize transformations, duplication, deletion; unify naming via core/naming.py.
   - [x] Add docstrings and examples for each public controller method.

15. [x] Visuals update pathway and state applier consistency
   - [x] ui/scene/state_applier.py: ensure there is a single pathway to apply model -> QGraphicsItem updates; controllers should invoke this instead of UI directly setting graphics item properties.
   - [x] Replace direct item.setRotation/Scale/Z calls in UI with calls routed through state_applier or controller methods that delegate there.
   - [x] Tests: verify that modifying rotation/scale/z via controller updates both model and visuals deterministically.

16. [x] Selection model and highlight strategy
   - [x] Replace scattered calls to scene.selectedItems()/setSelected with a selection model managed by controllers and a thin adapter that highlights items.
   - [x] Provide APIs: select_object(name), select_puppet(name), clear_selection(), get_selection().
   - [x] Ensure Inspector reads selection from the selection model, not from the scene.

17. [x] Performance: onion skin and large scenes
- [x] Audit ui/onion_skin.py and tests/test_onion_perf.py; add toggles via SettingsService (onion_pixmap_mode, onion_pixmap_scale already present) and ensure they are applied by controllers, not UI.
- [x] Micro-benchmark large puppet scenes; cache heavy computations in controllers/state_applier where safe.
- [x] Add a regression test measuring basic performance expectations (time budget hints, not strict timing).

18. [x] Error reporting and user feedback
   - [x] Introduce a simple UI message adapter (protocol) for controllers to report non-fatal issues (e.g., failed positioning in library_ops) instead of logging only.
   - [x] Replace print/log-only in UI operations with routed notifications.

19. [x] Testing coverage improvements
- [x] Add tests for new controller facade APIs and selection model.
- [x] Add tests verifying UI no longer directly mutates core models or QGraphicsItems (use monkeypatch/mocks to assert calls go through controller/facade).
- [x] Add serialization tests for settings JSON version/namespace mismatch handling (controllers/settings_service.py already supports issues list).

20. [x] Logging and diagnostics
  - [x] Enforce usage of core/logging_config.py across UI and controllers; remove ad-hoc basicConfig calls if any.
  - [x] Standardize logger names per module and ensure debug logs in hot paths are minimal or gated.

21. [x] Developer ergonomics and linting
   - [x] Add lightweight pylint rules guidance to README or docs/ (no strict CI), focusing on R0801 (duplicate-code), C0114/5/6 (docstrings), and typing hints.
   - [x] Run pylint on controllers core ui and address the top offenders (long functions, too many locals/branches in SettingsManager and InspectorWidget).

22. [x] Documentation updates
  - [x] Update README.md with a brief overview of the layered architecture and how to run tests in headless Qt.
  - [x] Add diagrams (optional) to docs/ showing the flow: UI widget -> presenter/adapter -> controller/service -> core model -> state_applier -> visuals.

23. [x] Migration steps and deprecations
- [x] Mark direct UI access patterns (e.g., main_window.scene_model, object_manager.graphics_items) as deprecated in code comments with TODOs pointing to facade methods.
- [x] Stage refactors in small PR-sized chunks: Inspector first, then SceneView, LibraryOps, then SettingsManager.
- [x] Keep existing tests green at each step; add incremental tests as new APIs are introduced.

24. [x] Clean edges discovered during refactor
   - [x] Replace magic strings for kinds ("object", "puppet", "background") with Enum in core/types.py and update users accordingly.
   - [x] Centralize name formatting for puppet members (e.g., f"{name}:{member}") via core/naming.py helpers to avoid stringly-typed keys.
