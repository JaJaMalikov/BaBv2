from PySide6.QtCore import QSettings

import macronotron


def test_qsettings_scope_set_by_create_app(_app):
    # Call create_app to ensure scope is enforced even if a QApplication exists
    macronotron.create_app([])
    s = QSettings()
    assert s.organizationName() == "JaJa"
    assert s.applicationName() == "Macronotron"
