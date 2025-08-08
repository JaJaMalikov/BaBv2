import './style.css';
import { SceneModel } from './core/sceneModel';
import { Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER } from './core/puppetModel';
import { SvgLoader } from './core/svgLoader';

async function main() {
  const app = document.querySelector<HTMLDivElement>('#app')!;
  app.innerHTML = '<h1>BaBv2 TS/Vite Port</h1>';
  const loader = await SvgLoader.fromUrl('/assets/wesh.svg');
  app.appendChild(loader.svg);
  const puppet = new Puppet();
  puppet.buildFromSvg(loader, PARENT_MAP, PIVOT_MAP, Z_ORDER);
  const scene = new SceneModel();
  scene.addPuppet('manu', puppet);
  console.log('Loaded puppet with members:', Object.keys(puppet.members));
}

main();

