export class SceneObject {
  name: string;
  objType: string;
  filePath: string;
  x: number;
  y: number;
  rotation: number;
  scale: number;
  attachedTo: [string, string] | null;

  constructor(name: string, objType: string, filePath: string, x = 0, y = 0, rotation = 0, scale = 1) {
    this.name = name;
    this.objType = objType;
    this.filePath = filePath;
    this.x = x;
    this.y = y;
    this.rotation = rotation;
    this.scale = scale;
    this.attachedTo = null;
  }

  attach(puppetName: string, memberName: string) {
    this.attachedTo = [puppetName, memberName];
  }

  detach() {
    this.attachedTo = null;
  }
}

export class Keyframe {
  index: number;
  objects: Record<string, any>;
  puppets: Record<string, any>;

  constructor(index: number) {
    this.index = index;
    this.objects = {};
    this.puppets = {};
  }
}

export class SceneModel {
  puppets: Record<string, any>;
  objects: Record<string, SceneObject>;
  background: SceneObject | null;
  keyframes: Record<number, Keyframe>;
  currentFrame: number;
  startFrame: number;
  endFrame: number;
  fps: number;

  constructor() {
    this.puppets = {};
    this.objects = {};
    this.background = null;
    this.keyframes = {};
    this.currentFrame = 0;
    this.startFrame = 0;
    this.endFrame = 100;
    this.fps = 24;
  }

  addPuppet(name: string, puppet: any) {
    this.puppets[name] = puppet;
  }

  removePuppet(name: string) {
    delete this.puppets[name];
  }

  addObject(obj: SceneObject) {
    this.objects[obj.name] = obj;
  }

  removeObject(name: string) {
    delete this.objects[name];
  }

  attachObject(objName: string, puppetName: string, memberName: string) {
    const obj = this.objects[objName];
    if (obj) {
      obj.attach(puppetName, memberName);
    }
  }

  detachObject(objName: string) {
    const obj = this.objects[objName];
    if (obj) {
      obj.detach();
    }
  }

  addKeyframe(index: number) {
    let kf = this.keyframes[index];
    if (!kf) {
      kf = new Keyframe(index);
      this.keyframes[index] = kf;
    }

    for (const [name, obj] of Object.entries(this.objects)) {
      kf.objects[name] = { ...obj };
    }

    for (const [puppetName, puppet] of Object.entries(this.puppets)) {
      const puppetState: Record<string, any> = {};
      for (const memberName of Object.keys(puppet.members || {})) {
        puppetState[memberName] = { rotation: 0, pos: [0, 0] };
      }
      kf.puppets[puppetName] = puppetState;
    }

    this.keyframes = Object.fromEntries(
      Object.entries(this.keyframes).sort((a, b) => Number(a[0]) - Number(b[0]))
    );
    return kf;
  }

  removeKeyframe(index: number) {
    delete this.keyframes[index];
  }

  goToFrame(index: number) {
    this.currentFrame = index;
  }

  exportJson(): string {
    const data = {
      settings: {
        start_frame: this.startFrame,
        end_frame: this.endFrame,
        fps: this.fps
      },
      puppets: Object.keys(this.puppets),
      objects: Object.fromEntries(
        Object.entries(this.objects).map(([k, v]) => [k, { ...v }])
      ),
      keyframes: Object.values(this.keyframes).map(kf => ({
        index: kf.index,
        objects: kf.objects,
        puppets: kf.puppets
      }))
    };
    return JSON.stringify(data, null, 2);
  }

  importJson(json: string) {
    let data: any;
    try {
      data = JSON.parse(json);
    } catch (e) {
      console.error('Erreur lors du chargement du JSON', e);
      return;
    }

    const settings = data.settings || {};
    this.startFrame = settings.start_frame ?? 0;
    this.endFrame = settings.end_frame ?? 100;
    this.fps = settings.fps ?? 24;

    this.keyframes = {};
    const loaded = data.keyframes || [];
    for (const kfData of loaded) {
      const index = kfData.index;
      if (index !== undefined) {
        const newKf = new Keyframe(index);
        newKf.objects = kfData.objects || {};
        newKf.puppets = kfData.puppets || {};
        this.keyframes[index] = newKf;
      }
    }

    this.keyframes = Object.fromEntries(
      Object.entries(this.keyframes).sort((a, b) => Number(a[0]) - Number(b[0]))
    );
  }
}
