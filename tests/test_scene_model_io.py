import json
from core.scene_model import SceneModel, SceneObject

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
