# Improvement Tasks Checklist

A logically ordered, actionable checklist covering architectural and code-level improvements.

1. [x] Establish baseline developer tooling and quality gates
   - [x] Add ruff/black configuration in pyproject.toml (consistent style, imports, and lint rules)
   - [x] Introduce mypy with a permissive baseline (incrementally tighten, enable strict in core/ first)
   - [x] Create a pre-commit config (black, ruff, mypy, pytest -q on changed paths)

2. [x] Define logging and error-handling standards
   - [x] Centralize logging configuration (formatter, levels, module filters) in a single bootstrap module
   - [x] Replace broad exception handlers (except Exception) with narrower, contextual handling in controllers and UI
   - [x] Ensure user-facing error reporting paths (dialogs/toasts) are distinct from developer logs
   - [x] Add structured log context for frame index, object/puppet names, and operation type

3. [x] Strengthen typing and protocol boundaries
   - [x] Expand typing.Protocol usage for all UI collaborators (TimelineWidgetProtocol, ObjectViewAdapterProtocol, InspectorWidgetProtocol)
   - [x] Add missing type annotations across controllers/ and ui/scene/
   - [x] Enable mypy for core/ as strict; fix revealed issues (Dict[str, Any] → TypedDict/dataclasses where appropriate)
   - [x] Add type-safe aliases for scene state maps (e.g., PuppetState, ObjectState)

4. [x] Core model invariants, validation, and serialization
   - [x] Document and enforce invariants in SceneModel (frame indices monotonic, unique object names, consistent attachments)
   - [x] Introduce schema/versioning for exported JSON (SceneModel.export_json/import_json) with a version field and migration hook
   - [x] Harden validate_* in core/scene_validation.py and ensure they are called at persistence boundaries
   - [x] Improve error messages and recovery when loading invalid scenes (partial load with warnings)

5. [x] SvgLoader robustness and test coverage
   - [x] Normalize namespace handling and unit parsing (px, %, etc.) with clear fallbacks
   - [x] Cache QSvgRenderer instances and consider lazy initialization for performance
   - [x] Add guards and explicit exceptions for missing/invalid groups and viewBox anomalies
   - [x] Create unit tests with malformed SVGs and edge cases (missing id, nested groups, non-numeric dimensions)

6. [ ] Puppet model API clarity and validation
   - [x] Add docstrings and examples for Puppet.build_from_svg, normalize_variants, and validate_svg_structure
   - [x] Validate parent/child relations and pivot references with actionable error messages
   - [ ] Replace ad-hoc maps with typed dataclasses for member/variant structures where feasible
   - [ ] Unit tests for hierarchy construction, child map computation, and variant normalization

7. [ ] Refactor SettingsManager (ui/settings_manager.py ~850+ lines)
   - [ ] Extract a pure SettingsService (load/save/keys/schema) decoupled from Qt widgets
   - [ ] Extract a dialog presenter/adapter responsible for binding settings to UI controls
   - [ ] Define a settings schema (dataclass + defaults) and centralize QSettings key namespacing
   - [ ] Add import/export validation and error reporting (profile format version)
   - [ ] Add unit tests for default loading, round-trips, and migration of keys

8. [ ] SceneController and services boundaries
   - [ ] Ensure SceneService remains Qt-agnostic and has a narrow, cohesive API
   - [ ] Move any direct graphics item assumptions out of controllers into adapters
   - [ ] Add docstrings and diagrams showing data flow: UI → Controller → Service → Model → View update

9. [ ] Onion skin performance and configurability
   - [ ] Introduce a cache layer for per-frame onion clones (reuse between updates when topology unchanged)
   - [ ] Option to render onion skins as pixmaps at reduced resolution for performance
   - [ ] Make opacity and frame-span configurable via settings with sane defaults
   - [ ] Profile and add a micro-benchmark for update_onion_skins across N keyframes and M items

10. [ ] Object and puppet operations consistency
    - [x] Centralize name uniquifying logic (unique_puppet_name, object duplicates) in a shared utility
    - [x] Ensure deep-copy semantics for duplication (state, z-order, variants) are consistent
    - [x] Replace magic numbers/strings (z offsets, handle sizes) with named constants or settings
    - [x] Add tests for duplicate/delete/attach/detach flows across frames

11. [x] Scene IO and path handling
    - [x] Standardize path resolution (project-relative vs absolute) and validate existence on load
    - [x] Add file dialog helpers with last-used directory persistence and filters
    - [x] Ensure export/import embed version and gracefully ignore unknown future fields

12. [ ] Testing improvements and coverage expansion
    - [ ] Increase unit test coverage for core and controllers; add regression tests for known bugs
    - [ ] Add headless UI tests using Qt’s offscreen platform + xvfb in CI
    - [ ] Parameterize tests for multiple assets (SVGs, JSON scenes) and edge conditions
    - [ ] Introduce smoke tests for startup_sequence and basic user flows

13. [x] Documentation upgrades
    - [x] Enrich ARCHITECTURE.md with sequence diagrams for key flows (keyframe add, onion update, attach object)
    - [x] Add CONTRIBUTING.md with coding style, commit message conventions, and PR checklist
    - [x] Document settings schema and keys in docs/settings.md
    - [x] Add troubleshooting guide for common runtime issues (Qt platform plugin, SVG rendering)

14. [x] Packaging and environment
    - [x] Define a project entry point in pyproject.toml (console/script entry)
    - [x] Pin minimal versions in requirements.txt; add dev-requirements (ruff, black, mypy, pytest-cov)
    - [x] Provide a Makefile or tasks.py for common tasks (lint, test, run, package)

15. [ ] UX and accessibility
    - [ ] Ensure keyboard navigation and focus visibility in key widgets (timeline, scene)
    - [ ] Externalize user-facing strings and prepare for i18n (Qt tr())
    - [ ] Persist window layouts, dock states, and last-used options reliably with schema validation

16. [ ] Performance and responsiveness
    - [ ] Audit main-thread long operations; move heavy work (SVG parsing, export) off the UI thread with QtConcurrent/QThread
    - [ ] Add progress feedback for long-running tasks (exports/imports)
    - [ ] Add lightweight profiling hooks and a developer flag to print frame timing

17. [ ] Code hygiene and dead code removal
    - [ ] Remove unused imports, dead code paths, and redundant logging
    - [ ] Normalize file/module naming (snake_case) and signal naming conventions per ARCHITECTURE.md
    - [ ] Add missing docstrings for public functions and classes
