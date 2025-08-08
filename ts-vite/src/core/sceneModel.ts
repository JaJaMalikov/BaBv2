export interface SceneObjectState {
  x: number;
  y: number;
  rotation: number;
  scale: number;
  attachedTo: [string, string] | null;
}

export class SceneObject {
  name: string;
  objType: string;
  filePath: string;
  x: number;
  y: number;
  rotation: number;
  scale: number;
  attachedTo: [string, string] | null;

  constructor(
    name: string,
    objType: string,
    filePath: string,
    x = 0,
    y = 0,
    rotation = 0,
    scale = 1.0
  ) {
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
  objects: Record<string, SceneObjectState>;
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
      kf.objects[name] = {
        x: obj.x,
        y: obj.y,
        rotation: obj.rotation,
        scale: obj.scale,
        attachedTo: obj.attachedTo,
      };
    }
    for (const [puppetName, puppet] of Object.entries(this.puppets)) {
      kf.puppets[puppetName] = puppet.getState ? puppet.getState() : {};
    }
    this.keyframes = Object.fromEntries(
      Object.entries(this.keyframes).sort(
        (a, b) => Number(a[0]) - Number(b[0])
      )
    );
    return kf;
  }

  removeKeyframe(index: number) {
    delete this.keyframes[index];
  }

  goToFrame(index: number) {
    this.currentFrame = index;
  }

  exportJson() {
    const data = {
      settings: {
        start_frame: this.startFrame,
        end_frame: this.endFrame,
        fps: this.fps,
      },
      puppets: Object.keys(this.puppets),
      objects: Object.fromEntries(
        Object.entries(this.objects).map(([k, v]) => [k, { ...v }])
      ),
      keyframes: Object.values(this.keyframes).map((kf) => ({
        index: kf.index,
        objects: kf.objects,
        puppets: kf.puppets,
      })),
    };
    return JSON.stringify(data, null, 2);
  }

  importJson(json: string) {
    try {
      const data = JSON.parse(json);
      const settings = data.settings || {};
      this.startFrame = settings.start_frame ?? 0;
      this.endFrame = settings.end_frame ?? 100;
      this.fps = settings.fps ?? 24;
      this.keyframes = {};
      for (const kfData of data.keyframes || []) {
        const kf = new Keyframe(kfData.index);
        kf.objects = kfData.objects || {};
        kf.puppets = kfData.puppets || {};
        this.keyframes[kf.index] = kf;
      }
      this.keyframes = Object.fromEntries(
        Object.entries(this.keyframes).sort(
          (a, b) => Number(a[0]) - Number(b[0])
        )
      );
    } catch (e) {
      console.error('Failed to load scene:', e);
    }
  }
}

