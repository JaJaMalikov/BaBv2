"""Main entry point for the Macronotron application."""

import sys
from typing import List

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.styles import apply_stylesheet


def create_app(argv: List[str]) -> QApplication:
    """Créer (ou récupérer) l'instance QApplication, définir la portée de QSettings, et appliquer le thème.

    Garantit que QSettings() se résolve à la portée JaJa/Macronotron dans toute l'application.
    """
    # Establish QSettings application scope early (docs/tasks.md Task 1)
    QCoreApplication.setOrganizationName("JaJa")
    QCoreApplication.setApplicationName("Macronotron")

    app = QApplication.instance() or QApplication(argv)
    apply_stylesheet(app)
    return app


def main(argv: List[str]) -> int:
    """Main entry point. Returns exit code."""
    app = create_app(argv)
    macronotron = MainWindow()
    macronotron.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
