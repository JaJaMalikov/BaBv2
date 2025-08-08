import './style.css';
import { SvgLoader } from './core/SvgLoader';
import { Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER } from './core/PuppetModel';

async function run() {
  const res = await fetch('/assets/wesh.svg');
  const svgText = await res.text();
  const loader = new SvgLoader(svgText);
  const puppet = new Puppet();
  puppet.buildFromSvg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER);
  console.log('Puppet loaded', puppet);
}

run();

document.querySelector<HTMLDivElement>('#app')!.innerHTML = `
  <h1>TS/Vite Port</h1>
  <p>Open the console to inspect the puppet model.</p>
`;
