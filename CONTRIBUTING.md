# Contributing to BaBv2

Thank you for your interest in improving BaBv2. This document summarizes how to propose changes while keeping the codebase reliable and friendly to new contributors.

## Prerequisites
- Python 3.9+ (compatible with PySide6)
- Install runtime deps:
  - pip install -r requirements.txt
- Install dev tools (optional but recommended for contributors):
  - pip install -r dev-requirements.txt

## Running the application
- From the repo root: python macronotron.py
- Or via the console entry (after an editable install): macronotron

## Running tests
- Headless Qt is configured by tests/conftest.py (QT_QPA_PLATFORM=offscreen). Just run:
  - pytest -q
- Run a single file: pytest -q tests/test_scene_model_io.py
- Show stdout: pytest -s
- For UI tests that instantiate Qt widgets, request the _app fixture:
  ```python
  def test_label_text(_app):
      ...
  ```

## Coding style
- Keep logic in core/ and controllers/; keep ui/ lean. Prefer Qt-agnostic services.
- Black and Ruff are configured in pyproject.toml (line-length 100). Before pushing:
  - black .
  - ruff check .
- Type checking via mypy (strict for core):
  - mypy core controllers ui macronotron.py

## Commit message conventions
- Use conventional, concise prefixes:
  - feat: user-facing feature
  - fix: bug fix
  - docs: documentation only
  - refactor: code refactor (no behavior change)
  - test: add or adjust tests
  - chore: tooling, deps, CI
- Scope is optional, e.g., fix(core): ensure shortest-arc rotation
- Body should explain the why and any notable trade-offs.

## Pull request checklist
- [ ] Tests pass locally (pytest -q)
- [ ] black and ruff show no issues
- [ ] mypy shows no new errors (esp. in core/)
- [ ] User-facing strings and icons validated if UI was changed
- [ ] Added or updated unit tests when behavior changes
- [ ] Updated docs/tasks.md if a checklist item was implemented

## Architectural principles
- See ARCHITECTURE.md for layering and signal/slot conventions
- Protocols in ui/protocols.py and related modules define UI/controller contracts
- JSON import/export must remain forward compatible (ignore unknown fields)

## Reporting issues
- Provide reproduction steps and, when possible, attach a minimal scene JSON or SVG assets that trigger the issue.
