"""Smoke test for application startup sequence and basic UI wiring.

This keeps to offscreen Qt via the _app fixture and avoids timers/sleeps.
"""

from ui.main_window import MainWindow


def test_startup_sequence_smoke(_app):
    win = MainWindow()

    # Core components exist and are wired
    assert hasattr(win, "scene_model")
    assert hasattr(win, "scene")
    assert hasattr(win, "object_controller")
    assert hasattr(win, "object_view_adapter")

    # Overlays and timeline are present
    assert hasattr(win, "overlays")
    assert hasattr(win, "timeline_widget")

    # Controllers/presenters created
    assert hasattr(win, "scene_controller")
    assert hasattr(win, "controller")  # AppController

    # Onion skin manager present and toggling is safe
    assert hasattr(win, "onion")
    assert win.onion.enabled is False
    win.set_onion_enabled(True)
    win.update_onion_skins()
    win.clear_onion_skins()
    win.set_onion_enabled(False)

    # Scene rectangle matches model defaults
    rect = win.scene.sceneRect()
    assert rect.width() == win.scene_model.scene_width
    assert rect.height() == win.scene_model.scene_height
