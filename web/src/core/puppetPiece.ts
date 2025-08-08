export class PuppetPiece {
  element: SVGGElement
  name: string
  pivot: [number, number]
  targetPivot?: [number, number]
  parentPiece: PuppetPiece | null = null
  children: PuppetPiece[] = []
  relToParent: [number, number] = [0, 0]
  localRotation = 0

  constructor(element: SVGGElement, name: string, pivot: [number, number], targetPivot?: [number, number]) {
    this.element = element
    this.name = name
    this.pivot = pivot
    this.targetPivot = targetPivot
  }

  setParentPiece(parent: PuppetPiece, relX = 0, relY = 0) {
    this.parentPiece = parent
    this.relToParent = [relX, relY]
    parent.children.push(this)
  }

  updateTransformFromParent() {
    if (!this.parentPiece) return
    const parentPivot = this.parentPiece.getScenePivot()
    const angle = (this.parentPiece.localRotation * Math.PI) / 180
    const [dx, dy] = this.relToParent
    const cos = Math.cos(angle)
    const sin = Math.sin(angle)
    const rotatedDx = dx * cos - dy * sin
    const rotatedDy = dx * sin + dy * cos
    const x = parentPivot[0] + rotatedDx - this.pivot[0]
    const y = parentPivot[1] + rotatedDy - this.pivot[1]
    this.setTransform(x, y, this.parentPiece.localRotation + this.localRotation)
    for (const child of this.children) {
      child.updateTransformFromParent()
    }
  }

  rotatePiece(angleDegrees: number) {
    this.localRotation = angleDegrees
    if (this.parentPiece) {
      this.updateTransformFromParent()
    } else {
      this.setTransform(this.getPosition()[0], this.getPosition()[1], this.localRotation)
      for (const child of this.children) {
        child.updateTransformFromParent()
      }
    }
  }

  setTransform(x: number, y: number, rotation: number) {
    this.element.setAttribute(
      'transform',
      `translate(${x} ${y}) rotate(${rotation} ${this.pivot[0]} ${this.pivot[1]})`
    )
  }

  getPosition(): [number, number] {
    const transform = this.element.getAttribute('transform') || ''
    const match = /translate\(([-0-9.]+) ([ -0-9.]+)\)/.exec(transform)
    if (match) return [parseFloat(match[1]), parseFloat(match[2])]
    return [0, 0]
  }

  getScenePivot(): [number, number] {
    const [x, y] = this.getPosition()
    const angle = (this.localRotation * Math.PI) / 180
    const cos = Math.cos(angle)
    const sin = Math.sin(angle)
    const px = x + this.pivot[0] * cos - this.pivot[1] * sin
    const py = y + this.pivot[0] * sin + this.pivot[1] * cos
    return [px, py]
  }
}
