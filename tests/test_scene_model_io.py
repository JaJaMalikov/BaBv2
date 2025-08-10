import json
from core.scene_model import SceneModel, SceneObject


def test_attach_detach_object():
    scene = SceneModel()
    obj = SceneObject("box", "image", "box.png")
    scene.add_object(obj)

    scene.attach_object("box", "p", "hand")
    assert scene.objects["box"].attached_to == ("p", "hand")

    scene.detach_object("box")
    assert scene.objects["box"].attached_to is None


def test_add_keyframe_snapshot_and_order():
    scene = SceneModel()
    obj = SceneObject("ball", "image", "ball.png", x=1)
    scene.add_object(obj)

    scene.add_keyframe(10)
    obj.x = 5
    scene.add_keyframe(0)

    assert [kf.index for kf in scene.keyframes.values()] == [0, 10]
    assert scene.keyframes[10].objects["ball"]["x"] == 1
    assert scene.keyframes[0].objects["ball"]["x"] == 5


def test_puppet_states_are_copied():
    scene = SceneModel()
    state = {"p": {"member": {"rot": 0}}}
    kf = scene.add_keyframe(0, puppet_states=state)
    state["p"]["member"]["rot"] = 90
    assert kf.puppets["p"]["member"]["rot"] == 0

def test_scene_object_roundtrip():
    obj = SceneObject("rock", "image", "rock.png", x=1, y=2, rotation=3, scale=0.5)
    obj.attach("p", "arm")
    data = obj.to_dict()
    cloned = SceneObject.from_dict(data)
    assert cloned.name == "rock"
    assert cloned.obj_type == "image"
    assert cloned.file_path == "rock.png"
    assert cloned.x == 1
    assert cloned.y == 2
    assert cloned.rotation == 3
    assert cloned.scale == 0.5
    assert cloned.attached_to == ("p", "arm")

def test_scene_object_export_import(tmp_path):
    scene = SceneModel()
    obj = SceneObject("tree", "image", "tree.png", x=10, y=20, rotation=5, scale=1.5)
    scene.add_object(obj)
    scene.add_keyframe(0)
    file_path = tmp_path / "scene.json"
    scene.export_json(file_path)

    scene2 = SceneModel()
    scene2.import_json(file_path)

    assert "tree" in scene2.objects
    loaded = scene2.objects["tree"]
    assert loaded.x == 10
    assert loaded.y == 20
    assert loaded.rotation == 5
    assert loaded.scale == 1.5
    assert loaded.file_path == "tree.png"
