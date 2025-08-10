from core.puppet_model import compute_child_map, Puppet, PuppetMember


def test_compute_child_map_basic():
    parent_map = {"b": "a", "c": "a", "d": "b"}
    assert compute_child_map(parent_map) == {"a": ["b", "c"], "b": ["d"]}


def test_get_first_child_pivot_and_handle_target():
    puppet = Puppet()
    root = PuppetMember("root")
    child = PuppetMember("child", pivot=(1, 2))
    root.add_child(child)
    puppet.members = {"root": root, "child": child}
    puppet.child_map = {"root": ["child"]}

    assert puppet.get_first_child_pivot("root") == (1, 2)
    assert puppet.get_first_child_pivot("child") == (None, None)
    assert puppet.get_handle_target_pivot("root") == (1, 2)
