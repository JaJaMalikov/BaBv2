import { Puppet } from './puppetModel'

export class SceneObject {
  name: string
  objType: string
  filePath: string
  x: number
  y: number
  rotation: number
  scale: number
  attachedTo: [string, string] | null = null

  constructor(name: string, objType: string, filePath: string, x = 0, y = 0, rotation = 0, scale = 1.0) {
    this.name = name
    this.objType = objType
    this.filePath = filePath
    this.x = x
    this.y = y
    this.rotation = rotation
    this.scale = scale
  }

  attach(puppetName: string, memberName: string) {
    this.attachedTo = [puppetName, memberName]
  }

  detach() {
    this.attachedTo = null
  }
}

export class Keyframe {
  index: number
  objects: Record<string, any> = {}
  puppets: Record<string, any> = {}

  constructor(index: number) {
    this.index = index
  }
}

export class SceneModel {
  puppets: Record<string, Puppet> = {}
  objects: Record<string, SceneObject> = {}
  background: SceneObject | null = null
  keyframes: Record<number, Keyframe> = {}
  currentFrame = 0
  startFrame = 0
  endFrame = 100
  fps = 24

  addPuppet(name: string, puppet: Puppet) {
    this.puppets[name] = puppet
  }

  removePuppet(name: string) {
    delete this.puppets[name]
  }

  addObject(obj: SceneObject) {
    this.objects[obj.name] = obj
  }

  removeObject(name: string) {
    delete this.objects[name]
  }

  attachObject(objName: string, puppetName: string, memberName: string) {
    const obj = this.objects[objName]
    if (obj) obj.attach(puppetName, memberName)
  }

  detachObject(objName: string) {
    const obj = this.objects[objName]
    if (obj) obj.detach()
  }

  addKeyframe(index: number) {
    let kf = this.keyframes[index]
    if (!kf) {
      kf = new Keyframe(index)
      this.keyframes[index] = kf
    }
    for (const [name, obj] of Object.entries(this.objects)) {
      kf.objects[name] = { ...obj }
    }
    for (const [pName, puppet] of Object.entries(this.puppets)) {
      const puppetState: Record<string, any> = {}
      for (const [memberName, member] of Object.entries(puppet.members)) {
        puppetState[memberName] = { pivot: member.pivot, zOrder: member.zOrder }
      }
      kf.puppets[pName] = puppetState
    }
    this.keyframes = Object.fromEntries(
      Object.entries(this.keyframes).sort((a, b) => Number(a[0]) - Number(b[0]))
    )
    return kf
  }

  removeKeyframe(index: number) {
    delete this.keyframes[index]
  }

  goToFrame(index: number) {
    this.currentFrame = index
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
    }
    return JSON.stringify(data, null, 2)
  }

  importJson(jsonStr: string) {
    try {
      const data = JSON.parse(jsonStr)
      const settings = data.settings || {}
      this.startFrame = settings.start_frame || 0
      this.endFrame = settings.end_frame || 100
      this.fps = settings.fps || 24
      this.keyframes = {}
      const loaded = data.keyframes || []
      for (const kfData of loaded) {
        const kf = new Keyframe(kfData.index)
        kf.objects = kfData.objects || {}
        kf.puppets = kfData.puppets || {}
        this.keyframes[kf.index] = kf
      }
      this.keyframes = Object.fromEntries(
        Object.entries(this.keyframes).sort((a, b) => Number(a[0]) - Number(b[0]))
      )
    } catch (e) {
      console.error('Failed to import JSON', e)
    }
  }
}
