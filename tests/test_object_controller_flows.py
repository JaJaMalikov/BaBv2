"""Extended tests for ObjectController flows across frames.

Covers duplicate, delete from current frame, and attach/detach across frames
without relying on Qt widgets.
"""
from __future__ import annotations

from controllers.object_controller import ObjectController, DUPLICATE_OFFSET
from core.scene_model import SceneModel, SceneObject


class DummyAdapter:
    def __init__(self) -> None:
        self.objects: dict[str, dict] = {}
        self.hidden: list[str] = []

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
        # Simulate hiding in UI
        self.hidden.append(name)
        self.objects.pop(name, None)

    # Attachments
    def attach_object_to_member(self, obj_name: str, puppet: str, member: str) -> dict:
        st = self.objects[obj_name]
        st["attached_to"] = (puppet, member)
        return dict(st)

    def detach_object(self, obj_name: str) -> dict:
        st = self.objects[obj_name]
        st["attached_to"] = None
        return dict(st)

    # Not used in these tests
    def create_object_from_file(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def create_light_object(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError


def _make_controller() -> tuple[ObjectController, DummyAdapter]:
    model = SceneModel()
    adapter = DummyAdapter()
    return ObjectController(model, adapter), adapter


def test_duplicate_object_deep_copy_and_offset() -> None:
    ctrl, adapter = _make_controller()
    base = SceneObject("obj", "svg", "a.svg", x=10, y=20, rotation=15, scale=2.0)
    base.z = 3
    ctrl.add_object(base)
    # Ensure a keyframe exists capturing initial state
    ctrl.snapshot_current_frame()

    ctrl.duplicate_object("obj")

    # Expect a new object with unique name
    names = set(ctrl.model.objects.keys())
    assert any(n.startswith("obj") and n != "obj" for n in names)
    dup_name = sorted(n for n in names if n != "obj")[0]

    dup = ctrl.model.objects[dup_name]
    assert dup.rotation == base.rotation
    assert dup.scale == base.scale
    assert dup.z == base.z
    assert dup.x == base.x + float(DUPLICATE_OFFSET)
    assert dup.y == base.y + float(DUPLICATE_OFFSET)

    # Keyframe should contain dup state at current frame
    kf = ctrl.model.keyframes[ctrl.model.current_frame]
    assert dup_name in kf.objects

    # Adapter should have graphics entry
    assert dup_name in adapter.objects


def test_delete_object_from_current_frame_affects_future_only() -> None:
    ctrl, adapter = _make_controller()
    obj = SceneObject("o", "svg", "b.svg")
    ctrl.add_object(obj)

    # Create keyframes at 0, 5, 10 with object present
    ctrl.model.add_keyframe(0, ctrl.capture_scene_state())
    ctrl.model.add_keyframe(5, ctrl.capture_scene_state())
    ctrl.model.add_keyframe(10, ctrl.capture_scene_state())

    # Move to frame 5 and delete from current frame
    ctrl.model.go_to_frame(5)
    ctrl.delete_object_from_current_frame("o")

    # Frames < 5 should keep the object
    assert "o" in ctrl.model.keyframes[0].objects
    # Frames >= 5 should have it removed
    assert "o" not in ctrl.model.keyframes[5].objects
    assert "o" not in ctrl.model.keyframes[10].objects

    # Adapter should have hidden record
    assert "o" in adapter.hidden


def test_attach_then_detach_on_later_frame_updates_keyframes_independently() -> None:
    ctrl, _ = _make_controller()
    obj = SceneObject("o2", "svg", "c.svg")
    ctrl.add_object(obj)

    # Frame 0 attach
    ctrl.model.go_to_frame(0)
    ctrl.attach_object_to_member("o2", "p", "hand")
    assert ctrl.model.objects["o2"].attached_to == ("p", "hand")
    assert ctrl.model.keyframes[0].objects["o2"]["attached_to"] == ("p", "hand")

    # Go to later frame and detach
    ctrl.model.go_to_frame(7)
    ctrl.detach_object("o2")

    # Ensure state at frame 7 is detached
    assert ctrl.model.keyframes[7].objects["o2"]["attached_to"] is None
    # Earlier frame 0 should still reflect attachment
    assert ctrl.model.keyframes[0].objects["o2"]["attached_to"] == ("p", "hand")
