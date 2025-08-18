# Repository Guidelines

## Project Structure & Module Organization
- `macronotron.py`: Entry point; starts the PySide6 app.
- `core/`: Domain and data layer (model). Pure Python logic and serialization live here (e.g., `scene_model.py`, `puppet_model.py`, `puppet_piece.py`).
- `ui/`: Presentation layer (views/controllers). Widgets and orchestration (e.g., `main_window.py`, `timeline_widget.py`, `scene/*`).
- `assets/`: Images/SVG and other static resources.
- `tests/`: Pytest suite (`test_*.py`). Keep tests mirroring module names.

## Build, Test, and Development Commands
- Install: `pip install -r requirements.txt` — PySide6, pytest, pylint.
- Run app: `python macronotron.py` — launches the UI (do not auto‑launch in scripts/CI).
- Run tests: `pytest -q` — executes unit and UI-adjacent tests.
- Lint: `pylint core ui macronotron.py` — honors repo `.pylintrc`.

## Coding Style & Naming Conventions
- Python 3; 4‑space indentation; line length ~88–100 chars.
- Prefer type hints and docstrings (see `core/scene_model.py`).
- Modules and files: `snake_case.py`; classes: `PascalCase`; functions/vars: `snake_case`.
- Architecture: keep business logic in `core/`; UI interactions and signals/slots in `ui/`. `MainWindow` binds model↔view.
- Linting: keep `pylint` clean or add targeted disables with rationale.

## Testing Guidelines
- Framework: `pytest` with `test_*.py` naming.
- Scope: unit tests for `core/` (pure logic) and thin integration tests for `ui/` behaviors (signals/state application).
- Add tests alongside features; mirror file names (e.g., `tests/test_scene_model_io.py`).
- Run locally: `pytest -q`; aim to cover new branches and error paths.

## Commit & Pull Request Guidelines
- Commits: imperative, concise subject; detailed body when changing behavior.
  - Example: `scene: add keyframe export validation`.
- PRs: focused scope, include description, rationale, screenshots/GIFs for UI changes, and references to issues.
- Checklist: tests passing, lints clean, docs updated when behavior or UI changes.

## Agent‑Specific Instructions
- Répondre en français.
- Respect MV architecture boundaries; integrate new UI via signals in `ui/timeline_widget.py` and slots in `ui/main_window.py` updating `core/scene_model.py`.
- Follow incremental workflow: small, reviewable changes. Do not auto‑run the app; the user launches `python macronotron.py`.
- After notable features, update `STATE_OF_THE_ART.md` to reflect current capabilities.
