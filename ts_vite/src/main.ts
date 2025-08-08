import { MainWindow } from './ui/mainWindow';

const app = new MainWindow();

const mountEl = document.getElementById('app');
if (mountEl) {
  app.mount(mountEl);
}
