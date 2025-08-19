# Project Improvement Plan

Context and sources
- The requested file docs/requirements.md is not present in the repository at the time of writing. To fulfill the intent of extracting key goals and constraints, this plan synthesizes information from the following authoritative documents: VISION.md, ARCHITECTURE.md, STATE_OF_THE_ART.md, README.md, and docs/tasks.md.
- The plan is organized by theme and provides rationale for each proposed change, with concrete, actionable recommendations mapped to current code structure (core/, controllers/, ui/, assets/, tests/).

Goals distilled from the documentation
- Product vision: A portable, live‑performance “digital puppet instrument” (targeting Raspberry Pi + ESP32 controller), with tactile control, immediacy, and hackability.
- Architectural goals: Strict layering (core, controllers, UI), protocol‑based boundaries, Qt‑agnostic core and services where possible, clear signal/slot conventions.
- Functional goals: Robust scene composition (multiple puppets/objects), reliable keyframe animation and interpolation (shortest‑arc angles), onion‑skin visualization, attachment/detachment semantics, inspector/library UX, JSON import/export with future‑proofing.
- Quality goals: Strong typing, validations, test coverage, performance responsiveness, and developer tooling (lint, type check, CI, coverage).
- UX goals: Overlay‑centric UI, configurable styles/icons, keyboard accessibility, predictable persistence of settings/layouts.
- Roadmap goals: Animation export, undo/redo, richer interpolation modes, controller hardware integration, portability to Raspberry Pi.

Key constraints
- Python 3.x compatible with PySide6 (3.9+ recommended). Tests run in headless Qt via QT_QPA_PLATFORM=offscreen set by tests/conftest.py.
- Runtime assets live in assets/ and ui_profile.json; run from repo root to preserve relative paths.
- Maintain strict separation: UI must not access core model directly; controllers mediate changes.
- Scene JSON must remain stable and forward‑compatible (unknown fields ignored gracefully).
- Keep logic in core/ and controllers/ to stay testable; keep ui/ lean. Avoid timers/sleeps in tests; prefer deterministic flows.

---

1. Core Model, Serialization, and Validation
Rationale
A stable, validated scene model and serialization layer is foundational for reliability, future migrations (including hardware control metadata), and portability to constrained devices (Raspberry Pi). Clear invariants and versioning reduce data‑corruption risks and enable safe feature growth.

Actions
- Introduce explicit schema/versioning in SceneModel export/import.
  - Add a version field in SceneModel.to_dict and handle migrations in import_json.
  - Provide a migrations registry to translate older versions.
- Document and enforce invariants in core/scene_model.py.
  - Frame indices monotonic; unique object and puppet IDs/names; consistent attachments across frames.
  - Add validation entry points in core/scene_validation.py and call at persistence boundaries (export/import).
- Strengthen typing for scene state maps.
  - Replace Dict[str, Any] with TypedDict or small dataclasses (e.g., PuppetState, ObjectState) for clarity and safety.
- Improve error handling and partial‑load behavior.
  - On import, accumulate warnings and load what’s valid where possible; return (ok, issues) or log structured messages with context (frame, object, operation).

2. Puppet and SVG Handling
Rationale
Puppet hierarchy correctness, variant selection, and robust SVG parsing are critical to consistent on‑screen results and to avoiding runtime failures when artists bring their own assets.

Actions
- Clarify and document Puppet API.
  - Add docstrings/examples for Puppet.build_from_svg, normalize_variants, validate_svg_structure.
  - Validate parent/child relations and pivots with actionable errors.
- Dataclass/typing upgrade.
  - Use dataclasses for member/variant structures; compute_child_map type hints; ensure compute_child_map is deterministic.
- SvgLoader robustness and caching.
  - Normalize namespace handling and unit parsing (px, %, etc.).
  - Add explicit exceptions/guards for missing groups/viewBox anomalies.
  - Cache QSvgRenderer or parsed structures to reduce repeated work; consider lazy init.
- Tests for malformed SVGs and edge cases.
  - Cover missing id, nested groups, non‑numeric dimensions, variant visibility rules.

3. Controllers and Service Boundaries
Rationale
Maintaining Qt‑agnostic services and slim controllers improves testability and prevents UI code from leaking into domain logic. Clear protocols document expectations and reduce Any usage.

Actions
- Ensure controllers/ services expose narrow, cohesive APIs.
  - Keep SceneService Qt‑agnostic; push QGraphics‑specific logic into adapters within ui/.
- Expand typing.Protocol usage across UI collaborators.
  - Define TimelineWidgetProtocol, ObjectViewAdapterProtocol, InspectorWidgetProtocol to formalize contracts.
- Centralize name‑uniquifying and duplication semantics.
  - Provide a shared utility for unique names and deep copy rules (state, z‑order, variants), used by both puppet and object operations.
- Document data flow with diagrams.
  - UI → Controller → Service → Model → View update, as a short section added to ARCHITECTURE.md.

4. UI/UX, Settings, and Overlays
Rationale
The overlay‑centric UX is a core differentiator. Making these widgets configurable, performant, and accessible improves live usability and aligns with the “instrument” vision.

Actions
- SettingsManager refactor into service + presenter.
  - Extract a pure SettingsService (schema, defaults, load/save, migrations) decoupled from Qt.
  - Keep a thin dialog binder for UI controls.
  - Centralize QSettings namespacing and add profile format versioning for import/export.
- Accessibility and keyboard navigation.
  - Ensure focus visibility and keyboard operation for timeline and scene; add shortcuts cheatsheet.
- Onion skin configurability and performance.
  - Cache per‑frame clones; optional pixmap downscaling; expose opacity and span as settings.
- Icon and theme customization hardening.
  - Validate custom icon overrides; document supported keys; ensure immediate refresh.

5. Scene I/O, Paths, and Persistence
Rationale
Consistent path handling and robust file dialogs reduce user friction and prevent broken projects when moving between systems or running on Raspberry Pi.

Actions
- Standardize path resolution (project‑relative vs absolute) with validation on load.
- Improve file dialogs
  - Persist last‑used directory; provide filters; respect headless contexts for tests.
- Future‑proof JSON
  - Embed version; ignore unknown future fields gracefully; add explicit error messages for missing required fields.

6. Playback, Interpolation, and Timeline
Rationale
Correct interpolation (especially angular shortest‑arc) and predictable visibility rules are central to animation quality.

Actions
- Confirm shortest‑arc interpolation for member and object rotations.
  - Keep normalized delta in [-180, 180] before lerp; add tests (e.g., 350° → 10° goes via −20°).
- Extend modes (future work)
  - Prepare hooks for easing functions; keep default as linear for determinism in tests.
- Timeline operations
  - Maintain copy/paste behavior; consider per‑object tracks as a later milestone.

7. Performance and Responsiveness
Rationale
Live performance and constrained hardware both require careful UI‑thread usage and simple, cache‑friendly operations.

Actions
- Audit long operations and move heavy work off the UI thread where safe (SVG parsing, exports) using QtConcurrent/QThread.
- Add lightweight profiling hooks.
  - Developer flag to print render/update timings; micro‑benchmark for onion skin updates.
- Cache frequently recomputed data (SVG renderers, transforms when topology unchanged).

8. Testing and Quality Tooling
Rationale
A reliable test suite and basic CI create a safety net for refactors and hardware‑driven changes.

Actions
- Expand unit tests in core/ and controllers/; keep UI tests as smoke/offscreen.
- Add ruff/black, mypy (strict for core/), pytest‑cov; introduce pre‑commit hooks.
- Configure CI (GitHub Actions) to run ruff, black --check, mypy, pytest -q with offscreen Qt; collect coverage and enforce a threshold.

9. Packaging and Portability
Rationale
Running on Raspberry Pi and distributing the desktop app requires predictable entry points and straightforward setup.

Actions
- Define a console/script entry point in pyproject.toml for macronotron.py.
- Split requirements into runtime and dev extras; pin minimal versions.
- Provide a Makefile or tasks.py for common flows (lint, test, run, package).
- Raspberry Pi notes
  - Document OS packages and GPU/Qt settings; guidance for headless vs attached display; Bluetooth permissions for ESP32 link.

10. Hardware Controller Integration (ESP32 + Pi)
Rationale
Supports the vision of a tactile instrument with immediate control and “hackability”.

Actions (Incremental)
- Phase 1: PoC data path
  - Define a simple BLE/SPP message schema for control events (encoder, joystick, buttons) and a Python receiver abstraction.
  - Map incoming events to controller methods (e.g., rotate member, add keyframe).
- Phase 2: Assignment UI
  - Add a small binding UI to assign physical controls to puppet members/actions; persist mapping in settings profile.
- Phase 3: Latency and robustness
  - Buffer/debounce on ESP32; verify event queue does not block UI thread on Pi; add reconnection strategy.

11. Documentation Upgrades
Rationale
Clear documentation accelerates contributions and preserves architectural intent.

Actions
- Enrich ARCHITECTURE.md with sequence diagrams for key flows.
- Add CONTRIBUTING.md with style, commit conventions, PR checklist.
- Document settings schema and keys (docs/settings.md).
- Troubleshooting guide (Qt offscreen issues, SVG rendering pitfalls, asset paths).

12. Risk Register and Mitigations
- Performance on Pi: mitigate with caching, off‑thread work, simplified themes; profile frequently.
- Asset variability: mitigate with stricter SVG validation and clear error messages.
- JSON evolution: mitigate with versioning + migrations; extensive import tests.
- Hardware flakiness: mitigate with resilient reconnect logic and test harnesses simulating input streams.
- UI regressions: mitigate with smoke tests and a stable UI protocol layer.

13. Milestones (suggested)
- M1: Core hardening (schema/versioning, validations, tests, lint/type tooling).
- M2: SVG/Puppet robustness + onion performance improvements; initial CI with coverage.
- M3: Settings refactor + documentation upgrades; packaging basics.
- M4: Animation export + groundwork for undo/redo; easing hooks (behind flags).
- M5: Hardware PoC and assignment UI; Raspberry Pi runbook; performance sweeps.

References to current code
- core/: scene_model.py, puppet_model.py, puppet_piece.py, svg_loader.py, scene_validation.py.
- controllers/: app_controller.py, scene_service.py, object_controller.py, playback_service.py.
- ui/: overlays (panels.py, draggable_widget.py), settings_manager.py, state_applier.py, views/*, scene/*.
- tests/: extensive coverage for scene I/O, playback, inspector refresh, keyframe copy/paste, validation.

Notes
- This plan aligns with docs/tasks.md’s checklist and consolidates it into a rationale‑driven roadmap. It intentionally keeps UI changes incremental to protect existing tests and headless execution defaults.
