import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.scene_model import SceneModel, SceneObject

def test_attach_detach_object():
    scene = SceneModel()
    obj = SceneObject("rock", "image", "rock.png")
    scene.add_object(obj)

    scene.attach_object("rock", "puppet", "arm")
    assert scene.objects["rock"].attached_to == ("puppet", "arm")

    scene.detach_object("rock")
    assert scene.objects["rock"].attached_to is None

def test_add_keyframe_captures_state_and_sorts():
    scene = SceneModel()
    obj = SceneObject("box", "image", "box.png", x=0, y=0)
    scene.add_object(obj)

    scene.add_keyframe(5)
    obj.x = 10
    scene.add_keyframe(2)

    assert list(scene.keyframes.keys()) == [2,5]
    assert scene.keyframes[5].objects["box"]["x"] == 0
    assert scene.keyframes[2].objects["box"]["x"] == 10
