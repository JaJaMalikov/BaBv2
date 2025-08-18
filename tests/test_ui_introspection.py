"""
Test d'introspection de l'interface utilisateur pour lister les widgets visibles.
"""

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget, QDialog

from ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    """Provide a QApplication instance for UI tests."""
    qapp = QApplication.instance() or QApplication([])
    return qapp


def _dump_widget_tree(widget: QWidget, indent: int = 0, lines: list[str] = None):
    """Construit récursivement une liste de chaînes représentant la hiérarchie des widgets."""
    if lines is None:
        lines = []

    if not widget.isVisible():
        return lines

    info = (
        f"{'  ' * indent}"
        f"- {widget.objectName() or '[no name]'} ({widget.__class__.__name__})"
    )
    lines.append(info)

    for child in widget.children():
        if isinstance(child, QWidget):
            _dump_widget_tree(child, indent + 1, lines)

    return lines


def test_dump_visible_widget_tree(app, capsys, monkeypatch):
    """
    Ce test instancie la MainWindow, l'affiche, ouvre la boîte de dialogue des paramètres,
    puis imprime un arbre de tous les composants QWidget visibles.
    Il "patch" QDialog.exec() pour éviter de bloquer le test.
    """
    # Remplacer temporairement la méthode bloquante exec() par open() qui ne l'est pas.
    monkeypatch.setattr(QDialog, "exec", lambda self: self.open())

    win = MainWindow()
    win.show()
    QApplication.processEvents()

    # Ouvre la boîte de dialogue des paramètres (maintenant non-bloquant)
    win.open_settings_dialog()
    QApplication.processEvents()

    lines = []
    # Parcourir toutes les fenêtres de haut niveau (MainWindow et QDialog)
    for widget in QApplication.topLevelWidgets():
        _dump_widget_tree(widget, lines=lines)

    with capsys.disabled():
        print("\n--- Arbre des widgets visibles de l'interface (avec QDialog) ---")
        for line in lines:
            print(line)
        print("--- Fin de l'arbre ---")

    # Une assertion simple pour que ce soit un test valide
    assert len(lines) > 1

    # Fermer le dialogue pour ne pas bloquer le testeur
    for widget in QApplication.topLevelWidgets():
        if isinstance(widget, QDialog):
            widget.close()
