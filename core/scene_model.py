from core.puppet_model import Puppet

class SceneObject:
    """
    Un objet générique de la scène (image, SVG, décor, etc.)
    Peut être libre ou attaché à un membre de pantin.
    """
    def __init__(self, name, obj_type, file_path, x=0, y=0, rotation=0, scale=1.0, z=0):
        self.name = name
        self.obj_type = obj_type  # "image", "svg", "puppet"
        self.file_path = file_path
        self.x = x
        self.y = y
        self.rotation = rotation
        self.scale = scale
        self.z = z
        self.attached_to = None  # ("puppet_name", "member_name") ou None

    def attach(self, puppet_name, member_name):
        self.attached_to = (puppet_name, member_name)

    def detach(self):
        self.attached_to = None

    def to_dict(self):
        """Sérialise l'objet pour l'export JSON."""
        return {
            "name": self.name,
            "obj_type": self.obj_type,
            "file_path": self.file_path,
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "scale": self.scale,
            "z": self.z,
            "attached_to": self.attached_to,
        }

    @classmethod
    def from_dict(cls, data):
        """Construit un ``SceneObject`` depuis une structure dict."""
        obj = cls(
            name=data.get("name"),
            obj_type=data.get("obj_type"),
            file_path=data.get("file_path"),
            x=data.get("x", 0),
            y=data.get("y", 0),
            rotation=data.get("rotation", 0),
            scale=data.get("scale", 1.0),
            z=data.get("z", 0),
        )
        attached = data.get("attached_to")
        if attached is not None:
            obj.attached_to = tuple(attached)
        return obj

class Keyframe:
    """
    Snapshot de l'état de la scène à un temps donné
    """
    def __init__(self, index):
        self.index = index
        self.objects = {}  # name -> état (position, rotation, scale, attachment, etc.)
        self.puppets = {} # puppet_name -> { member_name -> { rot: ..., pos: ...} }

class SceneModel:
    def __init__(self):
        self.puppets = {}    # name -> Puppet instance
        self.objects = {}    # name -> SceneObject
        self.keyframes = {}  # index -> Keyframe
        self.current_frame = 0
        self.start_frame = 0
        self.end_frame = 100
        self.fps = 24
        self.scene_width = 1920
        self.scene_height = 1080
        self.background_path = None

    # -----------------------------
    # PUPPETS ET OBJETS
    # -----------------------------
    def add_puppet(self, name, puppet: Puppet):
        self.puppets[name] = puppet

    def remove_puppet(self, name):
        self.puppets.pop(name, None)

    def add_object(self, scene_object: SceneObject):
        self.objects[scene_object.name] = scene_object

    def remove_object(self, name):
        self.objects.pop(name, None)

    # -----------------------------
    # ATTACHEMENT
    # -----------------------------
    def attach_object(self, obj_name, puppet_name, member_name):
        obj = self.objects.get(obj_name)
        if obj:
            obj.attach(puppet_name, member_name)

    def detach_object(self, obj_name):
        obj = self.objects.get(obj_name)
        if obj:
            obj.detach()

    # -----------------------------
    # KEYFRAMES ET TIMELINE
    # -----------------------------
    def add_keyframe(self, index, puppet_states=None):
        kf = self.keyframes.get(index)
        if not kf:
            kf = Keyframe(index)
            self.keyframes[index] = kf

        for name, obj in self.objects.items():
            kf.objects[name] = obj.to_dict()

        kf.puppets = puppet_states or {}

        self.keyframes = dict(sorted(self.keyframes.items()))
        return kf

    def remove_keyframe(self, index):
        self.keyframes.pop(index, None)

    def go_to_frame(self, index):
        self.current_frame = index
        # La restauration de l'état se fera dans la MainWindow
        # qui a accès aux objets graphiques.

    # -----------------------------
    # IMPORT/EXPORT
    # -----------------------------
    def to_dict(self):
        return {
            "settings": {
                "start_frame": self.start_frame,
                "end_frame": self.end_frame,
                "fps": self.fps,
                "scene_width": self.scene_width,
                "scene_height": self.scene_height,
                "background_path": self.background_path,
            },
            "puppets": list(self.puppets.keys()),
            "objects": {k: v.to_dict() for k, v in self.objects.items()},
            "keyframes": [
                {
                    "index": kf.index,
                    "objects": kf.objects,
                    "puppets": kf.puppets,
                }
                for kf in self.keyframes.values()
            ],
        }

    def from_dict(self, data):
        settings = data.get("settings", {})
        self.start_frame = settings.get("start_frame", 0)
        self.end_frame = settings.get("end_frame", 100)
        self.fps = settings.get("fps", 24)
        self.scene_width = settings.get("scene_width", 1920)
        self.scene_height = settings.get("scene_height", 1080)
        self.background_path = settings.get("background_path")

        self.objects.clear()
        for name, obj_data in data.get("objects", {}).items():
            obj_data["name"] = name
            self.objects[name] = SceneObject.from_dict(obj_data)

        self.keyframes.clear()
        for kf_data in data.get("keyframes", []):
            index = kf_data.get("index")
            if index is None:
                continue
            new_kf = Keyframe(index)
            new_kf.objects = kf_data.get("objects", {})
            new_kf.puppets = kf_data.get("puppets", {})
            self.keyframes[index] = new_kf

        self.keyframes = dict(sorted(self.keyframes.items()))

    def export_json(self, file_path):
        import json
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def import_json(self, file_path):
        import json
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Erreur lors du chargement du fichier : {e}")
            return
        self.from_dict(data)

