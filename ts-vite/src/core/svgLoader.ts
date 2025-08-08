export class SvgLoader {
  svg: SVGSVGElement;

  constructor(svg: SVGSVGElement) {
    this.svg = svg;
  }

  static async fromUrl(url: string) {
    const res = await fetch(url);
    const text = await res.text();
    const div = document.createElement('div');
    div.innerHTML = text;
    const svg = div.querySelector('svg') as SVGSVGElement;
    if (!svg) throw new Error('Invalid SVG');
    return new SvgLoader(svg);
  }

  getGroups(): string[] {
    const groups: string[] = [];
    this.svg.querySelectorAll('g[id]').forEach((g) => {
      const id = g.getAttribute('id');
      if (id) groups.push(id);
    });
    return groups;
  }

  getGroupBoundingBox(id: string): [number, number, number, number] | null {
    const elem = this.svg.querySelector(`#${id}`) as SVGGraphicsElement | null;
    if (!elem) return null;
    const box = elem.getBBox();
    return [box.x, box.y, box.x + box.width, box.y + box.height];
    }

  getPivot(id: string): [number, number] {
    const bbox = this.getGroupBoundingBox(id);
    if (!bbox) return [0, 0];
    const [xMin, yMin, xMax, yMax] = bbox;
    return [(xMin + xMax) / 2, (yMin + yMax) / 2];
  }

  getGroupOffset(id: string): [number, number] | null {
    const bbox = this.getGroupBoundingBox(id);
    if (!bbox) return null;
    return [bbox[0], bbox[1]];
  }

  getSvgViewBox(): number[] {
    const vb = this.svg.getAttribute('viewBox');
    if (vb) {
      return vb.split(/\s+/).map((n) => parseFloat(n));
    }
    const width = parseFloat(this.svg.getAttribute('width') || '0');
    const height = parseFloat(this.svg.getAttribute('height') || '0');
    return [0, 0, width, height];
  }
}

