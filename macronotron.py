import sys
import logging
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.styles import apply_stylesheet

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Apply the "Rêve Éveillé" theme
    apply_stylesheet(app)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
