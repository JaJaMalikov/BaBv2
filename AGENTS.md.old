# Repository Guidelines

## Project Structure & Module Organization
- `core/`: scene and puppet domain logic (`scene_model.py`, `puppet_model.py`, `puppet_piece.py`, `svg_loader.py`).
- `ui/`: Qt widgets and application shell (`main_window.py`, `timeline_widget.py`, `inspector_widget.py`).
- `assets/`: SVG assets used by the UI and tests.
- `tests/`: pytest test suite (`test_*.py`).
- Top level: `macronotron.py` (entry point), `demo.json`/`test_anim.json` (sample data), `requirements.txt`, `pyproject.toml`.

## Build, Test, and Development Commands
- Create env: `python -m venv .venv && source .venv/bin/activate`.
- Install deps: `pip install -r requirements.txt`.
- Run app: `python macronotron.py` (launches the PySide6 GUI).
- Run tests: `pytest -q` (headless; GUI tests set `QT_QPA_PLATFORM=offscreen`).

## Coding Style & Naming Conventions
- Python, 4‑space indentation, follow PEP 8.
- Naming: modules `lower_snake_case.py`; classes `PascalCase`; functions/vars `snake_case`.
- Keep UI concerns in `ui/` and model/IO logic in `core/`. Favor small, focused functions.
- No enforced formatter in repo; if you use one locally, prefer Black + Ruff defaults and keep diffs minimal.

## Testing Guidelines
- Framework: pytest. Place tests under `tests/` and name files `test_*.py`.
- Cover serialization/import/export in `core/` and interactions exercised by the GUI. Example: `pytest tests/test_scene_model_io.py -q`.
- GUI tests run offscreen; in CI set `QT_QPA_PLATFORM=offscreen` if needed: `export QT_QPA_PLATFORM=offscreen`.

## Commit & Pull Request Guidelines
- Commits: concise, imperative subject; optional Conventional Commits prefixes (`feat:`, `fix:`, `refactor:`) are welcome.
- PRs: clear description, rationale, and scope; link related issues. For UI changes, include screenshots or short clips.
- Keep changes scoped; update docs/tests when you change behavior or structure.

## Security & Configuration Tips
- Keep assets local; avoid hard‑coding absolute paths. Prefer repo‑relative paths in JSON scenes.
- Don’t commit machine‑specific files (e.g., `*.user`, caches). Respect `.gitignore`.
