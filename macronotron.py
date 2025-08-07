import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from qt_material import apply_stylesheet

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    apply_stylesheet(app, theme='dark_red.xml')
    window.show()
    sys.exit(app.exec())
