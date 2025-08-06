from core.puppet_model import Puppet

class SceneObject:
    """
    Un objet générique de la scène (image, SVG, décor, etc.)
    Peut être libre ou attaché à un membre de pantin.
    """
    def __init__(self, name, obj_type, file_path, x=0, y=0, rotation=0, scale=1.0):
        self.name = name
        self.obj_type = obj_type  # "image", "svg", "puppet"
        self.file_path = file_path
        self.x = x
        self.y = y
        self.rotation = rotation
        self.scale = scale
        self.attached_to = None  # ("puppet_name", "member_name") ou None

    def attach(self, puppet_name, member_name):
        self.attached_to = (puppet_name, member_name)

    def detach(self):
        self.attached_to = None

class Keyframe:
    """
    Snapshot de l'état de la scène à un temps donné
    """
    def __init__(self, index):
        self.index = index
        self.objects = {}  # name -> état (position, rotation, scale, attachment, etc.)

class SceneModel:
    def __init__(self):
        self.puppets = {}    # name -> Puppet instance
        self.objects = {}    # name -> SceneObject
        self.background = None  # SceneObject
        self.keyframes = []  # List[Keyframe]
        self.current_frame = 0

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
    def add_keyframe(self, index=None):
        if index is None:
            index = len(self.keyframes)
        kf = Keyframe(index)
        # Snapshot de l'état actuel
        for name, obj in self.objects.items():
            kf.objects[name] = obj.__dict__.copy()  # shallow copy (adapt as needed)
        # Pareil pour les puppets si tu veux snapshot leur pose
        self.keyframes.insert(index, kf)
        return kf

    def remove_keyframe(self, index):
        if 0 <= index < len(self.keyframes):
            self.keyframes.pop(index)

    def go_to_frame(self, index):
        if 0 <= index < len(self.keyframes):
            self.current_frame = index
            kf = self.keyframes[index]
            # Restaurer l'état des objets (à adapter si besoin)
            for name, state in kf.objects.items():
                if name in self.objects:
                    for key, value in state.items():
                        setattr(self.objects[name], key, value)
            # Idem pour les pantins (à compléter...)

    # -----------------------------
    # IMPORT/EXPORT
    # -----------------------------
    def export_json(self, file_path):
        import json
        data = {
            "puppets": list(self.puppets.keys()),  # à affiner
            "objects": {k: v.__dict__ for k, v in self.objects.items()},
            "keyframes": [
                {
                    "index": kf.index,
                    "objects": kf.objects
                }
                for kf in self.keyframes
            ]
        }
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def import_json(self, file_path):
        import json
        with open(file_path, "r") as f:
            data = json.load(f)
        # A compléter pour restaurer tout l'état...


