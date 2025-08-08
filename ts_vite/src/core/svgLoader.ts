export class SvgLoader {
  svgPath: string;

  constructor(svgPath: string) {
    this.svgPath = svgPath;
    // Real parsing is not implemented in this port.
  }

  getGroups(): string[] {
    return [];
  }

  getGroupBoundingBox(_groupId: string): [number, number, number, number] | null {
    return null;
  }

  getPivot(_groupId: string): [number, number] {
    return [0, 0];
  }
}
