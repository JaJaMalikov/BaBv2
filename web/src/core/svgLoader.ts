export class SvgLoader {
  private svg: SVGSVGElement

  constructor(svgContent: string) {
    const parser = new DOMParser()
    const doc = parser.parseFromString(svgContent, 'image/svg+xml')
    // documentElement is typed as Element; cast through unknown to SVGSVGElement
    this.svg = doc.documentElement as unknown as SVGSVGElement
  }

  getGroups(): string[] {
    const groups = Array.from(this.svg.querySelectorAll('g[id]'))
    return groups.map(g => g.id)
  }

  getGroupElement(id: string): SVGGElement | null {
    return this.svg.querySelector(`g#${id}`)
  }

  getGroupBoundingBox(id: string): [number, number, number, number] | null {
    const elem = this.getGroupElement(id)
    if (!elem) return null
    const bbox = elem.getBBox()
    return [bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height]
  }

  getGroupOffset(id: string): [number, number] | null {
    const bbox = this.getGroupBoundingBox(id)
    if (!bbox) return null
    return [bbox[0], bbox[1]]
  }

  getPivot(id: string): [number, number] {
    const bbox = this.getGroupBoundingBox(id)
    if (!bbox) return [0, 0]
    const [x1, y1, x2, y2] = bbox
    return [(x1 + x2) / 2, (y1 + y2) / 2]
  }

  getSvgViewBox(): [number, number, number, number] {
    const viewBox = this.svg.getAttribute('viewBox')
    if (viewBox) {
      const nums = viewBox.split(/\s+/).map(parseFloat)
      if (nums.length === 4) return [nums[0], nums[1], nums[2], nums[3]]
    }
    const width = parseFloat(this.svg.getAttribute('width') || '0')
    const height = parseFloat(this.svg.getAttribute('height') || '0')
    return [0, 0, width, height]
  }

  getSvgElement(): SVGSVGElement {
    return this.svg
  }
}
