import os
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QImage, QColor


@pytest.fixture()
def _reset_qsettings():
    s = QSettings("JaJa", "Macronotron")
    # Save old values to restore after test
    old = {
        "icon_dir": s.value("ui/icon_dir"),
        "icon_color_normal": s.value("ui/icon_color_normal"),
        "icon_size": s.value("ui/icon_size"),
        "override_open": s.value("ui/icon_override/open"),
        "override_save": s.value("ui/icon_override/save"),
    }
    try:
        yield s, old
    finally:
        # Restore
        if old["icon_dir"] is None:
            s.remove("ui/icon_dir")
        else:
            s.setValue("ui/icon_dir", old["icon_dir"])
        if old["icon_color_normal"] is None:
            s.remove("ui/icon_color_normal")
        else:
            s.setValue("ui/icon_color_normal", old["icon_color_normal"])
        if old["icon_size"] is None:
            s.remove("ui/icon_size")
        else:
            s.setValue("ui/icon_size", old["icon_size"])
        if old["override_open"] is None:
            s.remove("ui/icon_override/open")
        else:
            s.setValue("ui/icon_override/open", old["override_open"])
        if old["override_save"] is None:
            s.remove("ui/icon_override/save")
        else:
            s.setValue("ui/icon_override/save", old["override_save"])
        s.sync()


def _write_svg(path: Path, inner: str) -> None:
    # Minimal standalone SVG wrapper; 10x10 viewport
    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'>
      {inner}
    </svg>
    """
    path.write_text(svg.strip(), encoding="utf-8")


def test_icon_bitmap_override_bypasses_tinting(tmp_path, _reset_qsettings, _app):
    s, _old = _reset_qsettings
    # Prepare a black 10x10 PNG
    png_path = tmp_path / "black.png"
    img = QImage(10, 10, QImage.Format_ARGB32)
    img.fill(QColor(0, 0, 0))
    assert img.save(str(png_path))

    # Settings: red tint and size 10
    s.setValue("ui/icon_color_normal", "#FF0000")
    s.setValue("ui/icon_size", 10)
    s.setValue("ui/icon_override/save", str(png_path))
    s.sync()

    from ui import icons as app_icons

    app_icons.clear_cache()
    icon = app_icons.get_icon("save")
    pm = icon.pixmap(10, 10)
    color = pm.toImage().pixelColor(5, 5)

    # Expect the pixel to remain black (bitmap not tinted)
    assert color.red() == 0 and color.green() == 0 and color.blue() == 0


def test_icon_override_precedence_over_icon_dir(tmp_path, _reset_qsettings, _app):
    s, _old = _reset_qsettings

    # icon_dir provides an SVG that renders nothing (transparent)
    dir_path = tmp_path / "icons"
    dir_path.mkdir()
    empty_svg = dir_path / "open.svg"
    _write_svg(empty_svg, "")

    # per-icon override provides a solid rectangle covering the viewport
    override_svg = tmp_path / "override_open.svg"
    _write_svg(override_svg, "<rect x='0' y='0' width='10' height='10' fill='#000' />")

    s.setValue("ui/icon_dir", str(dir_path))
    s.setValue("ui/icon_override/open", str(override_svg))
    s.setValue("ui/icon_color_normal", "#00FF00")  # green tint for SVG
    s.setValue("ui/icon_size", 10)
    s.sync()

    from ui import icons as app_icons

    app_icons.clear_cache()
    icon = app_icons.get_icon("open")
    pm = icon.pixmap(10, 10)
    color = pm.toImage().pixelColor(5, 5)

    # Expect a non-transparent pixel (override SVG wins and renders content)
    assert color.alpha() > 0
