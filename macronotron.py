"""Main entry point for the Macronotron application."""

import sys
from pathlib import Path
from typing import List

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.styles import apply_stylesheet
from ui.ui_profile import UIProfile


def create_app(argv: List[str]) -> tuple[QApplication, UIProfile]:
    """Crée (ou récupère) l'instance QApplication et applique le thème."""
    app = QApplication.instance() or QApplication(argv)
    profile_path = Path("ui_profile.json")
    profile = UIProfile.import_json(str(profile_path))
    apply_stylesheet(app, profile)
    return app, profile


def main(argv: List[str]) -> int:
    """Point d'entrée principal de l'application. Retourne un code de sortie."""
    app, profile = create_app(argv)
    macronotron = MainWindow(profile)
    macronotron.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
