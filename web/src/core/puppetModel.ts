import { SvgLoader } from './svgLoader'

export const PARENT_MAP: Record<string, string | null> = {
  "torse": null,
  "cou": "torse",
  "tete": "cou",
  "epaule_droite": "torse",
  "haut_bras_droite": "epaule_droite",
  "coude_droite": "haut_bras_droite",
  "avant_bras_droite": "coude_droite",
  "main_droite": "avant_bras_droite",
  "epaule_gauche": "torse",
  "haut_bras_gauche": "epaule_gauche",
  "coude_gauche": "haut_bras_gauche",
  "avant_bras_gauche": "coude_gauche",
  "main_gauche": "avant_bras_gauche",
  "hanche_droite": "torse",
  "cuisse_droite": "hanche_droite",
  "genou_droite": "cuisse_droite",
  "tibia_droite": "genou_droite",
  "pied_droite": "tibia_droite",
  "hanche_gauche": "torse",
  "cuisse_gauche": "hanche_gauche",
  "genou_gauche": "cuisse_gauche",
  "tibia_gauche": "genou_gauche",
  "pied_gauche": "tibia_gauche"
}

export const PIVOT_MAP: Record<string, string> = {
  "tete": "cou",
  "haut_bras_droite": "epaule_droite",
  "avant_bras_droite": "coude_droite",
  "haut_bras_gauche": "epaule_gauche",
  "avant_bras_gauche": "coude_gauche",
  "cuisse_droite": "hanche_droite",
  "tibia_droite": "genou_droite",
  "cuisse_gauche": "hanche_gauche",
  "tibia_gauche": "genou_gauche",
  "cou": "cou",
  "epaule_droite": "epaule_droite",
  "coude_droite": "coude_droite",
  "epaule_gauche": "epaule_gauche",
  "coude_gauche": "coude_gauche",
  "hanche_droite": "hanche_droite",
  "genou_droite": "genou_droite",
  "hanche_gauche": "hanche_gauche",
  "genou_gauche": "genou_gauche",
  "torse": "torse"
}

export const Z_ORDER: Record<string, number> = {
  "torse": 0,
  "cou": -1,
  "tete": -1,
  "epaule_droite": 2,
  "haut_bras_droite": -1,
  "coude_droite": 2,
  "avant_bras_droite": 2,
  "main_droite": 3,
  "epaule_gauche": 2,
  "haut_bras_gauche": -1,
  "coude_gauche": 2,
  "avant_bras_gauche": 2,
  "main_gauche": 3,
  "hanche_droite": -1,
  "cuisse_droite": -2,
  "genou_droite": 2,
  "tibia_droite": 2,
  "pied_droite": 3,
  "hanche_gauche": -1,
  "cuisse_gauche": -2,
  "genou_gauche": 2,
  "tibia_gauche": 2,
  "pied_gauche": 3
}

function computeChildMap(parentMap: Record<string, string | null>): Record<string, string[]> {
  const childMap: Record<string, string[]> = {}
  for (const [child, parent] of Object.entries(parentMap)) {
    if (parent) {
      if (!childMap[parent]) childMap[parent] = []
      childMap[parent].push(child)
    }
  }
  return childMap
}

export class PuppetMember {
  name: string
  parent: PuppetMember | null = null
  children: PuppetMember[] = []
  pivot: [number, number]
  bbox: [number, number, number, number]
  zOrder: number

  constructor(name: string, pivot: [number, number], bbox: [number, number, number, number], zOrder: number) {
    this.name = name
    this.pivot = pivot
    this.bbox = bbox
    this.zOrder = zOrder
  }

  addChild(child: PuppetMember) {
    this.children.push(child)
    child.parent = this
  }
}

export class Puppet {
  members: Record<string, PuppetMember> = {}
  childMap: Record<string, string[]> = {}

  buildFromSvg(loader: SvgLoader, parentMap: Record<string, string | null>, pivotMap?: Record<string, string>, zOrderMap?: Record<string, number>) {
    this.childMap = computeChildMap(parentMap)
    const groups = loader.getGroups()
    for (const groupId of groups) {
      if (!(groupId in parentMap)) continue
      const bbox = loader.getGroupBoundingBox(groupId) || [0,0,0,0]
      const pivotGroup = pivotMap && pivotMap[groupId] ? pivotMap[groupId] : groupId
      const pivot = loader.getPivot(pivotGroup)
      const z = zOrderMap && zOrderMap[groupId] !== undefined ? zOrderMap[groupId] : 0
      this.members[groupId] = new PuppetMember(groupId, pivot, bbox, z)
    }
    for (const [child, parent] of Object.entries(parentMap)) {
      const childMember = this.members[child]
      const parentMember = parent ? this.members[parent] : null
      if (childMember && parentMember) {
        parentMember.addChild(childMember)
      }
    }
  }

  getRootMembers(): PuppetMember[] {
    return Object.values(this.members).filter(m => m.parent === null)
  }

  getFirstChildPivot(name: string): [number, number] | null {
    const childNames = this.childMap[name] || []
    if (childNames.length > 0) {
      const target = this.members[childNames[0]]
      if (target) return target.pivot
    }
    return null
  }

  getHandleTargetPivot(name: string): [number, number] | null {
    return this.getFirstChildPivot(name)
  }

  printHierarchy(member?: PuppetMember, indent: string = '') {
    if (!member) {
      for (const root of this.getRootMembers()) {
        this.printHierarchy(root, indent)
      }
    } else {
      console.log(`${indent}- ${member.name} (pivot=${member.pivot} z=${member.zOrder})`)
      for (const child of member.children) {
        this.printHierarchy(child, indent + '  ')
      }
    }
  }
}
