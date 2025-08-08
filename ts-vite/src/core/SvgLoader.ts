export class SvgLoader {
  private doc: Document;

  constructor(svgText: string) {
    const parser = new DOMParser();
    this.doc = parser.parseFromString(svgText, 'image/svg+xml');
  }

  getGroups(): string[] {
    const groups = Array.from(this.doc.querySelectorAll('g[id]')) as SVGGElement[];
    return groups.map(g => g.id);
  }

  getGroupBoundingBox(groupId: string): [number, number, number, number] | null {
    const element = this.doc.getElementById(groupId) as SVGGraphicsElement | null;
    if (!element) return null;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.style.position = 'absolute';
    svg.style.visibility = 'hidden';
    const clone = element.cloneNode(true) as SVGGraphicsElement;
    svg.appendChild(clone);
    document.body.appendChild(svg);
    const box = clone.getBBox();
    document.body.removeChild(svg);
    return [box.x, box.y, box.x + box.width, box.y + box.height];
  }

  getPivot(groupId: string): [number, number] {
    const box = this.getGroupBoundingBox(groupId);
    if (!box) return [0, 0];
    const [xMin, yMin, xMax, yMax] = box;
    return [(xMin + xMax) / 2, (yMin + yMax) / 2];
  }

  getSvgViewbox(): number[] {
    const viewBox = this.doc.documentElement.getAttribute('viewBox');
    if (viewBox) {
      return viewBox.split(/\s+/).map(n => parseFloat(n));
    }
    const width = parseFloat(this.doc.documentElement.getAttribute('width') || '0');
    const height = parseFloat(this.doc.documentElement.getAttribute('height') || '0');
    return [0, 0, width, height];
  }
}
