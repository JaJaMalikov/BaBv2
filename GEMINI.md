# Gemini Project Context: BABv2 (Macronotron)

## Project Overview

This project, internally named "Borne and the Bayrou - Disco MIX", is a 2D puppeteering and animation tool built with Python and the PySide6 Qt framework. It allows users to load SVG files as puppets, define a hierarchical skeleton, and animate them using a keyframe-based timeline.

**Core Technologies:**
- **Language:** Python
- **UI Framework:** PySide6
- **UI Styling:** qt-material (`dark_red.xml` theme)
- **Testing Framework:** pytest

**Architecture:**

The application follows a Model-View-Controller-like pattern:
- **Model (`core/`):** `scene_model.py` holds the state of the entire animation (keyframes, timeline settings), while `puppet_model.py` defines the static structure of a puppet (bone hierarchy, pivots, Z-ordering).
- **View (`ui/`, `core/puppet_piece.py`):** `main_window.py` is the main application window. `timeline_widget.py` provides the interactive timeline. `puppet_piece.py` is the graphical `QGraphicsItem` representation of a single puppet part in the scene.
- **Controller (`ui/main_window.py`):** The `MainWindow` class contains the primary logic for handling user input, updating the model, and connecting UI elements to the underlying data.

## Building and Running

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application:**
    ```bash
    python macronotron.py
    ```

3.  **Run Tests:**
    ```bash
    pytest
    ```

## Development Conventions

- **Project Structure:** Code is organized into a `core` directory for business logic, a `ui` directory for graphical components, and a `tests` directory for unit tests. Maintain this separation.
- **Puppet Definition:** Puppets are defined from layers in an SVG file. The hierarchy, pivot points and Z-order are stored in `core/puppet_config.json` and loaded by `core/puppet_model.py`. To add a new puppet, update this configuration file.
- **Data Persistence:** The animation scene, including all keyframes and timeline settings (FPS, start/end frames), is serialized to a JSON file via the `SceneModel`.
- **UI Styling:** The UI is styled using `qt-material`. Changes should be tested against this styling.
- **User Preferences:** The user handles running the development server themselves. Do not execute commands like `npm run dev` or similar.
