"""Main entry point for the Macronotron application."""

import sys
from typing import List

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.styles import apply_stylesheet
from ui.settings_manager import load_active_profile


def create_app(argv: List[str]) -> QApplication:
    """Crée (ou récupère) l'instance QApplication et applique le thème."""
    app = QApplication.instance() or QApplication(argv)
    apply_stylesheet(app, load_active_profile())
    return app


def main(argv: List[str]) -> int:
    """Point d'entrée principal de l'application. Retourne un code de sortie."""
    app = create_app(argv)
    macronotron = MainWindow()
    macronotron.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
