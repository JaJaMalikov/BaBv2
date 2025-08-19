# Improvement Tasks Checklist

Note: Each item starts with a checkbox placeholder for tracking. Items are numbered for logical order; use sub-numbering for related subtasks.

[ ] 1. Define and enforce architectural boundaries across layers (core, controllers, ui).
[ ] 1.1 Add an import-linter (or similar) configuration to prevent forbidden imports (e.g., ui -> core, controllers -> core only, ui -> controllers only).
[ ] 1.2 Add a lightweight pytest check that runs import-linter with the repo to fail on boundary violations.
[ ] 1.3 Document allowed dependencies and examples in ARCHITECTURE.md (update the “Layers” and “Data flow” sections).

[ ] 2. Centralize settings keys/namespacing and usage across the codebase.
[ ] 2.1 Adopt controllers.settings_service.SettingsService.key(...) for QSettings key construction in all UI modules.
[ ] 2.2 Replace ad-hoc string literals for settings keys in ui/* with centralized helpers; add a test to assert key stability.

[ ] 3. Refactor ui/settings_manager.py into smaller, testable units.
[ ] 3.1 Extract dialog data binding to a presenter/adapter (see §7.2) and remove nested functions from open_dialog.
[ ] 3.2 Move import/export logic to a pure service (see §7.1/§7.3) and keep the manager focused on orchestration and QSettings bridge.
[ ] 3.3 Add unit tests that cover: load/save geometry, timeline visibility, toolbar overlay geometry, and shortcut persistence.
[ ] 3.4 Add error handling paths for malformed QSettings values (e.g., invalid QByteArray) with logged warnings (consistent logger usage).

[ ] 4. Strengthen SceneModel invariants and serialization.
[ ] 4.1 After import_json/from_dict, run _validate_invariants with clear error reporting; return False with messages collected for UI display.
[ ] 4.2 Add scene schema versioning constants and explicit migration steps in _migrate_data; unit-test a migration scenario.
[ ] 4.3 Improve typing of SceneSnapshot/ObjectStateMap/PuppetStateMap usages; add mypy-friendly annotations where missing.
[ ] 4.4 Add a round-trip property test: to_dict -> json -> from_dict maintains equality of keyframes and object attachments.

[ ] 5. Isolate Puppet SVG validation and enhance performance.
[ ] 5.1 Move validate_svg_structure out of core/puppet_model.py into a new core/svg_validation.py to separate concerns.
[ ] 5.2 Introduce caching of computed parent/child maps and pivots keyed by SVG path + mtime to avoid recomputation.
[ ] 5.3 Add tests for cycle detection, missing pivots, and invalid parent references (positive/negative tests).

[ ] 6. Improve SvgLoader robustness and caching.
[ ] 6.1 Key the renderer cache by (path, mtime, size) to avoid stale caches when the file changes in place.
[ ] 6.2 Provide XML parsing errors with element line/column when available; include group/pivot id context in messages.
[ ] 6.3 Add a fast-path for group bbox using viewBox + transform-free elements; unit-test deterministic bounding boxes.
[ ] 6.4 Expand malformed SVG tests (tests/test_svg_loader_malformed.py) with additional cases (missing viewBox, nested groups, invalid href).

[ ] 7. Settings system modernization and portability.
[ ] 7.1 Extract a pure SettingsService (no Qt) with dataclass schema and defaults for portable JSON profiles. (Present in controllers/settings_service.py; integrate across UI.)
[ ] 7.2 Extract a presenter/adapter for dialog bindings to onion-skin controls (and future tabs), mapping to/from schema. (Present in controllers/settings_presenter.py; wire into SettingsManager.)
[ ] 7.3 Implement JSON import/export via SettingsService (load_json/save_json) with version/namespace validation and issue reporting in the UI.
[ ] 7.4 Replace duplicate onion key handling by reusing presenter helpers; add tests verifying backward compatibility of legacy QSettings keys.
[ ] 7.5 Add a migration command in the UI: "Export current QSettings to JSON profile" and "Import JSON profile to QSettings" using the service.

[ ] 8. Decompose ui/views/timeline_widget.py for maintainability.
[ ] 8.1 Extract a TimelinePainter responsible only for drawing (no state/QSettings/etc.).
[ ] 8.2 Extract a small interaction/model class for selection, hover, drag, and keyframe sets; keep QWidget thin.
[ ] 8.3 Centralize timeline-related settings (colors, zoom, keyframe size) and load via SettingsService/keys.
[ ] 8.4 Add focused unit tests for coordinate transforms (_frame_to_x/_x_to_frame) and keyboard/mouse actions without a QPA server (tests use _app fixture).

[ ] 9. Unify logging and contextual diagnostics.
[ ] 9.1 Ensure all controllers use core.logging_config.log_with_context for structured logs on warning/error paths.
[ ] 9.2 Replace bare prints/logging calls in UI with module-level loggers and consistent messages (include op= and identifiers).
[ ] 9.3 Add a test that exercises a few error paths and asserts logs contain expected context keys.

[ ] 10. Strengthen type hints and protocols.
[ ] 10.1 Add Protocols for window/controller interfaces passed around (win has: scene_model, timeline_widget, playback_handler, etc.).
[ ] 10.2 Add type hints to public methods lacking annotations; run mypy optionally in dev (not enforced in CI yet).

[ ] 11. Expand and harden the test suite.
[ ] 11.1 Add tests for SettingsManager integration using the _app fixture: verify apply/import/export flows without touching real user directories.
[ ] 11.2 Add property-based tests (hypothesis) for SceneModel keyframe operations (insert/remove/go_to_frame monotonic behaviors).
[ ] 11.3 Add fuzz-like tests for SvgLoader group/pivot lookup using small synthetic SVG snippets.

[ ] 12. Performance improvements (measurable wins).
[ ] 12.1 Implement optional onion skin pixmap mode in OnionSkinManager with downscaling (see schema onion_pixmap_mode/onion_pixmap_scale); add toggles in settings dialog.
[ ] 12.2 Cache per-frame composite onion layers when camera/zoom unchanged; invalidate on scene change.
[ ] 12.3 Add a simple micro-benchmark script (under tests/perf/) to compare frame render times with/without pixmap mode.

[ ] 13. Improve UI startup and layout persistence.
[ ] 13.1 Ensure timeline dock visibility and floating state changes persist reliably across sessions; add regression tests.
[ ] 13.2 Make overlay toolbars raise_ calls resilient when overlays are absent; avoid attribute errors (defensive hasattr checks).

[ ] 14. Developer experience and tooling.
[ ] 14.1 Extend .pre-commit-config.yaml with black, isort, flake8/pylint hooks; document usage in README.
[ ] 14.2 Add a Makefile target: `make lint` and `make test` to streamline local dev flows.
[ ] 14.3 Optionally add GitHub Actions workflow to run tests and lint on pushes/PRs (if/when repo is hosted with CI).

[ ] 15. Documentation improvements.
[ ] 15.1 Update ARCHITECTURE.md with a diagram of settings flow: QSettings <-> Presenter <-> Dialog Widgets and JSON import/export via SettingsService.
[ ] 15.2 Add a small docs/settings.md explaining profile format (namespace, version, data) with examples and migration policy.
[ ] 15.3 Document testing tips for Qt in tests/README or ARCHITECTURE.md appendices (reuse conftest _app fixture, headless offscreen).

[ ] 16. Safety and error handling.
[ ] 16.1 Ensure file operations in import/export catch and surface errors to the UI with actionable messages; test file-not-found and invalid JSON cases.
[ ] 16.2 Standardize try/except patterns: catch specific exceptions where possible; log and continue gracefully.

[ ] 17. Code cleanup and consistency.
[ ] 17.1 Remove dead code and unused imports (run pylint hints); keep UI thin and move logic into controllers/core where feasible.
[ ] 17.2 Normalize naming conventions (English identifiers, consistent acronyms: kf/keyframe, bbox, etc.).
