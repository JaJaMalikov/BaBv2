import { SceneModel, SceneObject } from '../core/sceneModel';
import { Puppet, PARENT_MAP, PIVOT_MAP, Z_ORDER } from '../core/puppetModel';
import { TimelineWidget } from './timelineWidget';

export class MainWindow {
  sceneModel: SceneModel;
  timeline: TimelineWidget;
  root: HTMLElement | null = null;

  constructor() {
    this.sceneModel = new SceneModel();
    this.timeline = new TimelineWidget();

    // Example: preload puppet
    this.addPuppet('assets/wesh.svg', 'manu');
  }

  mount(element: HTMLElement) {
    this.root = element;
    this.timeline.mount(element);
  }

  addPuppet(svgPath: string, name: string) {
    const puppet = new Puppet();
    // SvgLoader usage not implemented; pass null to build from maps only
    puppet.buildFromSvg(null, PARENT_MAP, PIVOT_MAP, Z_ORDER);
    this.sceneModel.addPuppet(name, puppet);
  }

  addObject(filePath: string, objName: string, objType = 'image', x = 0, y = 0) {
    const obj = new SceneObject(objName, objType, filePath, x, y);
    this.sceneModel.addObject(obj);
  }
}
