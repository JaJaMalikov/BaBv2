"""Tests unitaires pour ``ObjectController`` sans dépendance à Qt."""

from controllers.object_controller import ObjectController
from core.scene_model import SceneModel, SceneObject


class DummyAdapter:
    """Adaptateur minimal simulant les opérations graphiques."""

    def __init__(self) -> None:
        self.objects: dict[str, dict] = {}

    # Capture
    def capture_puppet_states(self) -> dict:
        return {}

    def capture_visible_object_states(self) -> dict:
        return {k: dict(v) for k, v in self.objects.items()}

    # Items
    def add_object_graphics(self, obj: SceneObject) -> None:
        self.objects[obj.name] = {
            "x": obj.x,
            "y": obj.y,
            "rotation": obj.rotation,
            "scale": obj.scale,
            "z": obj.z,
            "attached_to": obj.attached_to,
        }

    def remove_object_graphics(self, name: str) -> None:
        self.objects.pop(name, None)

    def hide_object(self, name: str) -> None:
        self.objects.pop(name, None)

    # Attachements
    def attach_object_to_member(self, obj_name: str, puppet: str, member: str) -> dict:
        st = self.objects[obj_name]
        st["attached_to"] = (puppet, member)
        return dict(st)

    def detach_object(self, obj_name: str) -> dict:
        st = self.objects[obj_name]
        st["attached_to"] = None
        return dict(st)

    def create_object_from_file(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def create_light_object(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError


def _make_controller() -> ObjectController:
    model = SceneModel()
    adapter = DummyAdapter()
    return ObjectController(model, adapter)


def test_add_and_remove_object() -> None:
    ctrl = _make_controller()
    obj = SceneObject("test", "svg", "path.svg")
    ctrl.add_object(obj)
    assert "test" in ctrl.model.objects

    ctrl.remove_object("test")
    assert "test" not in ctrl.model.objects


def test_attach_and_detach_updates_model_and_keyframe() -> None:
    ctrl = _make_controller()
    obj = SceneObject("obj", "svg", "a.svg")
    ctrl.add_object(obj)
    ctrl.attach_object_to_member("obj", "pup", "hand")
    assert ctrl.model.objects["obj"].attached_to == ("pup", "hand")
    assert ctrl.model.keyframes[0].objects["obj"]["attached_to"] == ("pup", "hand")

    ctrl.detach_object("obj")
    assert ctrl.model.objects["obj"].attached_to is None
    assert ctrl.model.keyframes[0].objects["obj"]["attached_to"] is None


def test_capture_scene_state() -> None:
    ctrl = _make_controller()
    obj = SceneObject("o", "svg", "b.svg", x=1, y=2)
    ctrl.add_object(obj)
    state = ctrl.capture_scene_state()
    assert state["objects"]["o"]["x"] == 1
    assert state["objects"]["o"]["y"] == 2
