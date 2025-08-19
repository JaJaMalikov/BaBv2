# Development Guidelines (Project‑specific)

This document summarizes the practical, project‑specific information needed to build, test, and evolve this codebase efficiently.

Repository: BaBv2 (PySide6/pytest)


## 1) Build and configuration

- Python version: any modern Python 3.x supported by PySide6 (3.9+ recommended). No special build steps.
- Dependencies:
  - Install from the root:
    - pip install -r requirements.txt
- Running the app:
  - python macronotron.py
- Project metadata:
  - pyproject.toml is minimal; PySide6 project metadata is present, no custom build hooks.
- Runtime assets:
  - The UI references assets/ and ui_profile.json. Running from the repo root keeps relative paths valid.

Notes:
- No additional environment variables are required to run the application.
- For tests, a headless Qt configuration is automatically applied (see testing section below); do not override QT_QPA_PLATFORM unless you know what you’re doing.


## 2) Testing

Test framework: pytest (configured via tests/conftest.py).

- Headless Qt:
  - tests/conftest.py sets os.environ["QT_QPA_PLATFORM"] = "offscreen", so tests run without an X server.
  - It also provides a QApplication fixture named _app that can be requested by tests when creating widgets.

- Running tests:
  - All tests: pytest -q
  - Single file: pytest -q tests/test_scene_model_io.py
  - By keyword: pytest -q -k keyframe
  - Show stdout for UI tree dumps or debug prints: pytest -s

- Adding new tests:
  - Place files under tests/ and name them test_*.py. Use plain pytest style.
  - For UI code that touches Qt, request the _app fixture to ensure a QApplication exists. Example:

    ```python
    # tests/test_example_ui.py
    from PySide6.QtWidgets import QLabel

    def test_label_text(_app):  # ensures QApplication
        w = QLabel("Hello")
        assert w.text() == "Hello"
    ```

  - For file I/O round‑trips use pytest’s tmp_path fixture; avoid writing into the repo.
  - Prefer deterministic logic; avoid time.sleep and timers inside tests. Interact with widgets synchronously.

- Example minimal test (validated during authoring of this document):

  This example was created, executed successfully, and then removed to keep the repo clean. It demonstrates exercising the core SceneModel API and the JSON export/import path.

  ```python
  from core.scene_model import SceneModel

  def test_add_keyframe_and_export_import(tmp_path):
      scene = SceneModel()
      scene.add_keyframe(12)
      assert 12 in scene.keyframes

      json_path = tmp_path / "scene.json"
      scene.export_json(json_path)

      clone = SceneModel()
      ok = clone.import_json(json_path)
      assert ok is True
      assert 12 in clone.keyframes
  ```

- Current test suite status: as of 2025‑08‑19, the full suite passes locally (33 tests ~3s) under headless Qt.


## 3) Additional development information

Coding style and structure:
- The codebase is organized into layered modules:
  - core/: domain models, serialization, SVG/puppet handling.
  - controllers/: application logic and services mediating between UI and models.
  - ui/: PySide6 widgets, view adapters, and scene‑specific operations.
  - assets/: runtime images, icons, and puppet configuration used by the UI.
- Prefer extending core/ and controllers/ for logic and keep ui/ lean; this keeps logic testable without a GUI.
- Tests already cover core serialization, state application, playback, and minimal UI introspection. Follow the existing patterns for new features.

Qt/GUI testing tips:
- Use the _app fixture from tests/conftest.py for any test that instantiates Qt widgets. This prevents accidental creation of a second QApplication and ensures offscreen platform is active.
- Avoid relying on focus events or timers; trigger logic directly via controller methods or signals you emit synchronously.
- If you need to inspect widget hierarchies, replicate the pattern used in existing UI tests; prefer querying specific widgets rather than asserting large text dumps.

I/O and assets:
- When tests need files, use tmp_path to avoid polluting the repository and to keep runs hermetic.
- If referencing bundled assets, resolve paths relative to the repository root (Path(__file__).resolve().parents[1]) similar to tests/conftest.py.

Linting:
- pylint is listed in requirements; there is no strict configuration checked in. You can run:
  - pylint controllers core ui macronotron.py
  Adjust suppressions locally if needed; there’s no enforced CI in this repo.

Performance and reliability:
- Headless Qt via offscreen makes tests fast and reliable; keep this default.
- Keep new tests focused and deterministic. Prefer unit‑level tests in core/ and controllers/; UI tests should be smoke‑level unless necessary.

Release/packaging:
- Not configured. The app is run directly from sources. Any packaging should account for assets/ and ui_profile.json paths.
