"""Main entry point for the Macronotron application."""

import sys
import logging
from typing import List

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.styles import apply_stylesheet


logger = logging.getLogger(__name__)


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
    """Main entry point. Returns exit code.

    Supports a developer utility flag --reset-layout to clear persisted UI layout
    (geometry/layout keys) without launching the UI, as per docs/tasks.md.
    """
    # Developer utility: reset layout and exit
    if "--reset-layout" in argv:
        # Ensure QSettings scope is established
        create_app(argv)
        try:
            from ui.settings_manager import SettingsManager

            sm = SettingsManager(win=object())
            sm.clear()
            logger.info("Macronotron: cleared UI layout (geometry/layout keys) in QSettings.")
            return 0
        except Exception:  # log stack trace for debugging
            logger.exception("Macronotron: failed to reset layout")
            return 1

    app = create_app(argv)
    macronotron = MainWindow()
    macronotron.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
