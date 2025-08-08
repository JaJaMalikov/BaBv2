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

  constructor(name: string, pivotX = 0, pivotY = 0, targetPivotX?: number, targetPivotY?: number) {
    this.name = name;
    this.pivotX = pivotX;
    this.pivotY = pivotY;
    this.targetPivotX = targetPivotX;
    this.targetPivotY = targetPivotY;
  }

  setHandleVisibility(_visible: boolean) {
    // placeholder
  }

  setParentPiece(parent: PuppetPiece | null, relX = 0, relY = 0) {
    this.parentPiece = parent;
    this.relToParent = [relX, relY];
    if (parent && !parent.children.includes(this)) {
      parent.children.push(this);
    }
  }

  updateTransformFromParent() {
    // placeholder for hierarchical transformations
  }

  rotatePiece(angleDegrees: number) {
    this.localRotation = angleDegrees;
    if (this.parentPiece) {
      this.updateTransformFromParent();
    }
  }
}
