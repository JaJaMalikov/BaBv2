export class PuppetPiece {
  element: SVGGraphicsElement;
  name: string;
  pivotX: number;
  pivotY: number;
  parentPiece: PuppetPiece | null;
  children: PuppetPiece[];
  relToParent: [number, number];
  localRotation: number;

  constructor(
    element: SVGGraphicsElement,
    name: string,
    pivotX = 0,
    pivotY = 0
  ) {
    this.element = element;
    this.name = name;
    this.pivotX = pivotX;
    this.pivotY = pivotY;
    this.parentPiece = null;
    this.children = [];
    this.relToParent = [0, 0];
    this.localRotation = 0;
  }

  setParentPiece(parent: PuppetPiece | null, relX = 0, relY = 0) {
    this.parentPiece = parent;
    this.relToParent = [relX, relY];
    if (parent && !parent.children.includes(this)) {
      parent.children.push(this);
    }
  }

  updateTransformFromParent() {
    if (!this.parentPiece) return;
    const parent = this.parentPiece;
    const angleRad = (parent.localRotation * Math.PI) / 180;
    const [dx, dy] = this.relToParent;
    const cosA = Math.cos(angleRad);
    const sinA = Math.sin(angleRad);
    const rotatedDx = dx * cosA - dy * sinA;
    const rotatedDy = dx * sinA + dy * cosA;
    const x = parent.pivotX + rotatedDx - this.pivotX;
    const y = parent.pivotY + rotatedDy - this.pivotY;
    this.element.setAttribute(
      'transform',
      `translate(${x},${y}) rotate(${parent.localRotation + this.localRotation},${this.pivotX},${this.pivotY})`
    );
    for (const child of this.children) {
      child.updateTransformFromParent();
    }
  }

  rotatePiece(angleDegrees: number) {
    this.localRotation = angleDegrees;
    if (this.parentPiece) {
      this.updateTransformFromParent();
    } else {
      this.element.setAttribute(
        'transform',
        `rotate(${this.localRotation},${this.pivotX},${this.pivotY})`
      );
      for (const child of this.children) {
        child.updateTransformFromParent();
      }
    }
  }
}

