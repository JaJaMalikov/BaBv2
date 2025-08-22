"""Configuration for pytest."""

import sys
import os
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QDialog

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(autouse=True)
def _nonblocking_qdialog(monkeypatch):
    """Ensure QDialog.exec() is non-blocking across all UI tests.
    Replaces blocking exec() with open() so tests never hang on dialogs.
    """
    monkeypatch.setattr(QDialog, "exec", lambda self: self.open())


@pytest.fixture(scope="module")
def _app():
    """Provide a ``QApplication`` instance for UI tests."""
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp
