# Macronotron Improvement Tasks Checklist

A logically ordered, actionable checklist derived from .junie/guidelines.md and a scan of the current codebase. Each line starts with a checkbox placeholder.

1. [ ] Centralize all QSettings keys in a single module (e.g., ui/settings_keys.py) and replace string literals across the repo to avoid typos and drift.
2. [x] Audit all QSettings reads/writes and normalize types using ui.ui_profile._bool/_int/_float helpers; remove ad-hoc parsing scattered in modules (e.g., ui/settings_manager.py, ui/icons.py, ui/styles.py, ui/main_window.py).
3. [x] Scene IO paths policy: decide on relative vs absolute paths for puppet assets; implement normalization and document behavior; add tests for round-trip path handling.
4. [x] Architecture audit: ensure controllers do not persist UI state (no QSettings usage); refactor any violations to SettingsManager.
5. [ ] UI/model boundaries: audit ui/* for direct model mutations; route all model changes through controllers; add regression tests where issues were found.
6. [x] Playback service: verify timer cadence, play/pause/stop/loop behavior, and frame wrap logic; ensure signal names follow snake_case conventions; extend tests.
7. [x] Logging consistency: adopt module-level loggers (logging.getLogger(__name__)) and consistent levels/messages; lightly refactor modules emitting logging.basicConfig usage if any.
8. [x] Linting: add a pylintrc aligned with project conventions (signals naming, typing precision, hasattr checks) and integrate linting into CI. (Done: .pylintrc + .github/workflows/lint.yml)
9. [ ] Typing: introduce typing.Protocols for view contracts (ui/contracts.py) where missing and run mypy in CI; annotate hot paths for clarity.
10. [x] Documentation: expand ARCHITECTURE.md with testing strategy, QSettings schema (key list/type expectations), and scene IO contract.
11. [x] Menu order/visibility: ensure OverlayManager.apply_menu_settings respects both order and per-action visibility from QSettings; add tests for round-trip consistency.
12. [ ] Action registry: consolidate action key definitions and associated icons between ui/actions.py, ui/views/*/actions.py, and ui/menu_defaults.py; add a test that each action has an icon mapping.
13. [ ] Scene background/size actions: wire these actions to persist via SettingsManager and update ui/styles appropriately; add tests.
