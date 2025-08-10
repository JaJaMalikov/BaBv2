import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.append(str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from core.svg_loader import SvgLoader, translate_path
from core.puppet_model import compute_child_map, Puppet, PuppetMember

import tempfile

app = QApplication.instance() or QApplication([])

def create_simple_svg(tmpdir: Path):
    svg_content = """
    <svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'>
      <g id='g1'>
        <rect x='10' y='20' width='30' height='40' />
      </g>
      <g id='g2'>
        <circle cx='50' cy='50' r='10' />
      </g>
    </svg>
    """
    file_path = tmpdir / "test.svg"
    file_path.write_text(svg_content)
    return file_path

def test_svg_loader_basic_functions(tmp_path):
    svg_file = create_simple_svg(tmp_path)
    loader = SvgLoader(str(svg_file))

    groups = set(loader.get_groups())
    assert {"g1", "g2"} <= groups

    bbox = loader.get_group_bounding_box("g1")
    assert bbox == (10.0, 20.0, 40.0, 60.0)

    pivot = loader.get_pivot("g1")
    assert pivot == (25.0, 40.0)

def test_translate_path_preserves_whitespace():
    d = "M 10 20 L 30 40"
    translated = translate_path(d, 5, 10)
    assert translated == "M 5.0 10.0 L 25.0 30.0"

def test_compute_child_map_and_puppet_pivots():
    parent_map = {"root": None, "child1": "root", "child2": "root"}
    child_map = compute_child_map(parent_map)
    assert child_map == {"root": ["child1", "child2"]}

    puppet = Puppet()
    parent = PuppetMember("root", pivot=(0,0))
    child1 = PuppetMember("child1", pivot=(10,5))
    child2 = PuppetMember("child2", pivot=(20,0))
    puppet.members = {"root": parent, "child1": child1, "child2": child2}
    puppet.child_map = child_map

    assert puppet.get_first_child_pivot("root") == (10,5)
    assert puppet.get_handle_target_pivot("root") == (10,5)
    assert puppet.get_first_child_pivot("child1") == (None, None)
