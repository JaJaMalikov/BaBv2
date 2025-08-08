import { SvgLoader } from './core/svgLoader'
import { Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER } from './core/puppetModel'
import { PuppetPiece } from './core/puppetPiece'

async function init() {
  const resp = await fetch('/assets/wesh.svg')
  const svgText = await resp.text()
  const loader = new SvgLoader(svgText)
  const puppet = new Puppet()
  puppet.buildFromSvg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER)

  const app = document.getElementById('app')!
  app.innerHTML = loader.getSvgElement().outerHTML
  const svgElement = app.querySelector('svg') as SVGSVGElement

  const pieces: Record<string, PuppetPiece> = {}
  for (const [name, member] of Object.entries(puppet.members)) {
    const elem = svgElement.querySelector(`g#${name}`) as SVGGElement
    if (!elem) continue
    const offset = loader.getGroupOffset(name) || [0, 0]
    const target = puppet.getHandleTargetPivot(name)
    const piece = new PuppetPiece(elem, name, [member.pivot[0], member.pivot[1]], target || undefined)
    piece.setTransform(offset[0], offset[1], 0)
    pieces[name] = piece
  }

  for (const [name, piece] of Object.entries(pieces)) {
    const member = puppet.members[name]
    if (member.parent) {
      const parentPiece = pieces[member.parent.name]
      const parentMember = member.parent
      const relX = member.pivot[0] - parentMember.pivot[0]
      const relY = member.pivot[1] - parentMember.pivot[1]
      piece.setParentPiece(parentPiece, relX, relY)
    }
  }

  console.log('Puppet ready', puppet)
}

init()
