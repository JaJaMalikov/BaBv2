from __future__ import annotations

"""Shortcut loading helpers for SettingsManager."""

import logging
from typing import Any

from PySide6.QtCore import QSettings
from PySide6.QtGui import QKeySequence


def load(win: Any, org: str = "JaJa", app: str = "Macronotron") -> None:
    """Load keyboard shortcuts from QSettings and apply them to actions."""
    if not hasattr(win, "shortcuts"):
        return
    s = QSettings(org, app)
    s.beginGroup("shortcuts")
    for key, action in win.shortcuts.items():
        seq = s.value(key)
        if seq:
            try:
                ks = QKeySequence(seq)
                if ks.isEmpty():
                    logging.warning(
                        "Ignoring invalid shortcut sequence for %s: %r", key, seq
                    )
                else:
                    action.setShortcut(ks)
            except Exception as e:
                logging.warning("Failed to apply shortcut for %s: %r (%s)", key, seq, e)
    s.endGroup()
