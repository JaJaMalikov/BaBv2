export class PuppetPiece {
  name: string;
  pivotX: number;
  pivotY: number;
  targetPivotX?: number;
  targetPivotY?: number;
  parentPiece: PuppetPiece | null = null;
  children: PuppetPiece[] = [];
  relToParent: [number, number] = [0, 0];
  localRotation = 0;
  x = 0;
  y = 0;

  constructor(name: string, pivotX = 0, pivotY = 0, targetPivotX?: number, targetPivotY?: number) {
    this.name = name;
    this.pivotX = pivotX;
    this.pivotY = pivotY;
    this.targetPivotX = targetPivotX;
    this.targetPivotY = targetPivotY;
  }

  setParentPiece(parent: PuppetPiece, relX = 0, relY = 0) {
    this.parentPiece = parent;
    this.relToParent = [relX, relY];
    if (parent && !parent.children.includes(this)) {
      parent.children.push(this);
    }
  }

  setPosition(x: number, y: number) {
    this.x = x;
    this.y = y;
    for (const child of this.children) {
      child.updateTransformFromParent();
    }
  }

  getRotation(): number {
    return (this.parentPiece ? this.parentPiece.getRotation() : 0) + this.localRotation;
  }

  updateTransformFromParent() {
    if (!this.parentPiece) return;
    const parent = this.parentPiece;
    const parentRotation = parent.getRotation();
    const angleRad = (parentRotation * Math.PI) / 180;
    const [dx, dy] = this.relToParent;
    const cos = Math.cos(angleRad);
    const sin = Math.sin(angleRad);
    const rotatedDx = dx * cos - dy * sin;
    const rotatedDy = dx * sin + dy * cos;
    const sceneX = parent.x + rotatedDx;
    const sceneY = parent.y + rotatedDy;
    this.x = sceneX - this.pivotX;
    this.y = sceneY - this.pivotY;
    for (const child of this.children) {
      child.updateTransformFromParent();
    }
  }

  rotatePiece(angleDegrees: number) {
    this.localRotation = angleDegrees;
    if (this.parentPiece) {
      this.updateTransformFromParent();
    }
  }
}
