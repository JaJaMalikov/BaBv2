import sys
import logging
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from qt_material import apply_stylesheet

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    try:
        apply_stylesheet(app, theme='dark_red.xml')
    except Exception as e:
        logging.warning(f"Theme apply failed, continuing without qt-material: {e}")
    window.show()
    sys.exit(app.exec())
