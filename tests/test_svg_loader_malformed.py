from pathlib import Path

import pytest

from core.svg_loader import SvgLoader


def _write_svg(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "test.svg"
    p.write_text(content, encoding="utf-8")
    return p


def test_get_svg_viewbox_valid_and_fallbacks(tmp_path: Path):
    # Valid viewBox
    svg1 = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 200" width="100" height="200">
      <g id="a"></g>
    </svg>
    """
    path1 = _write_svg(tmp_path, svg1)
    loader1 = SvgLoader(str(path1))
    assert loader1.get_svg_viewbox() == [0.0, 0.0, 100.0, 200.0]

    # Malformed viewBox -> fallback to width/height, with px unit stripped
    svg2 = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 a b" width="50px" height="25">
      <g id="a"></g>
    </svg>
    """
    path2 = _write_svg(tmp_path, svg2)
    loader2 = SvgLoader(str(path2))
    assert loader2.get_svg_viewbox() == [0.0, 0.0, 50.0, 25.0]

    # No viewBox and percentage sizes -> fallback to zeros
    svg3 = """
    <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="50%">
      <g id="a"></g>
    </svg>
    """
    path3 = _write_svg(tmp_path, svg3)
    loader3 = SvgLoader(str(path3))
    assert loader3.get_svg_viewbox() == [0.0, 0.0, 0.0, 0.0]

    # Non-numeric width -> lenient numeric extraction should default to 0.0
    svg4 = """
    <svg xmlns="http://www.w3.org/2000/svg" width="foo" height="12px">
      <g id="a"></g>
    </svg>
    """
    path4 = _write_svg(tmp_path, svg4)
    loader4 = SvgLoader(str(path4))
    assert loader4.get_svg_viewbox() == [0.0, 0.0, 0.0, 12.0]


def test_get_groups_nested_and_missing_ids(tmp_path: Path):
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg">
      <g id="parent">
        <g id="child"><path d="M0 0 L10 10"/></g>
        <g><path d="M0 0 L5 5"/></g>
      </g>
      <g id="sibling"></g>
    </svg>
    """
    path = _write_svg(tmp_path, svg)
    loader = SvgLoader(str(path))
    groups = set(loader.get_groups())
    assert {"parent", "child", "sibling"}.issubset(groups)
    # Ensure group without id is not included
    assert not any(g == "" for g in groups)


def test_extract_group_missing_raises(tmp_path: Path):
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg">
      <g id="exists"><rect x="0" y="0" width="10" height="10"/></g>
    </svg>
    """
    path = _write_svg(tmp_path, svg)
    loader = SvgLoader(str(path))
    with pytest.raises(ValueError):
        loader.extract_group("does_not_exist", str(tmp_path / "out.svg"))
