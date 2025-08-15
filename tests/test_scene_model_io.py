"""Tests for scene model serialization and deserialization."""
import json

from core.scene_model import SceneModel, SceneObject


def test_scene_object_roundtrip():
    """Test that a SceneObject can be serialized and deserialized."""
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
    """Test that a scene with an object can be exported and imported."""
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


def test_import_json_invalid_file(tmp_path):
    """Test that importing an invalid JSON file fails gracefully."""
    scene = SceneModel()
    # créer un JSON invalide
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ not: valid json }")
    # l'import doit échouer et retourner False, sans exception
    ok = scene.import_json(bad_file)
    assert ok is False


def test_import_json_invalid_structure(tmp_path):
    """Test that importing a JSON file with an invalid structure fails gracefully."""
    scene = SceneModel()
    # État initial pour vérifier qu'il ne change pas en cas d'échec
    scene.start_frame = 1
    # structure invalide: objects est une liste, keyframes est un dict
    data = {
        "settings": {"start_frame": 0, "fps": 24},
        "objects": [1, 2, 3],  # invalide, doit être dict
        "keyframes": {"index": 0},  # invalide, doit être liste
    }
    file_path = tmp_path / "invalid_structure.json"
    file_path.write_text(json.dumps(data))

    ok = scene.import_json(file_path)
    assert ok is False
    # état non modifié
    assert scene.start_frame == 1
