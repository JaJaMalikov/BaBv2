from __future__ import annotations

from PySide6.QtCore import QSettings

from ui.styles import apply_stylesheet, get_theme_colors


def _reset_theme_key() -> None:
    s = QSettings("JaJa", "Macronotron")
    s.remove("ui/theme")


def test_high_contrast_palette_and_stylesheet(_app):
    _reset_theme_key()
    s = QSettings("JaJa", "Macronotron")
    s.setValue("ui/theme", "high contrast")

    # Apply stylesheet and verify key substrings are present
    apply_stylesheet(_app)
    css = _app.styleSheet()
    assert "background-color: #000000" in css
    assert "#FFD600" in css  # accent color presence

    # Verify theme colors used by non-stylesheet elements
    colors = get_theme_colors()
    assert colors["background"] == "#000000"
    assert colors["text"] == "#FFFFFF"
    assert colors["panel"] == "#000000"
    assert colors["accent"] == "#FFD600"

    _reset_theme_key()
