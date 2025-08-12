import sys
import logging
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    # No external theme dependency; styling handled internally
    window.show()
    sys.exit(app.exec())
