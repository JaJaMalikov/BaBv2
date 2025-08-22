"""Headless UI test to ensure puppet selection shows properties in Inspector."""

from pathlib import Path

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def test_puppet_selection_shows_properties(_app):
    """Selecting a puppet in the inspector should show the properties panel.

    Also verify that attachment rows (for objects) are hidden when a puppet is selected.
    """
    win = MainWindow()

    # Add a puppet to the scene
    puppet_path = str(Path("assets/pantins/manu.svg").resolve())
    win.scene_controller.add_puppet(puppet_path, "manu")

    # Ensure the inspector lists the puppet and select it
    lw = win.inspector_widget.list_widget
    idx = -1
    for i in range(lw.count()):
        if lw.item(i).text() == "manu":
            idx = i
            break
    assert idx >= 0, "Puppet 'manu' not found in inspector list"
    lw.setCurrentRow(idx)

    # Let Qt process the currentItemChanged signal
    QApplication.processEvents()

    insp = win.inspector_widget
    assert (
        insp.props_panel.isVisible()
    ), "Inspector properties panel should be visible for puppets"

    # Attachment rows should be hidden for puppets
    assert hasattr(insp, "attach_row") and not insp.attach_row.isVisible()
    assert hasattr(insp, "member_row") and not insp.member_row.isVisible()
    assert (
        hasattr(insp, "attach_actions_row") and not insp.attach_actions_row.isVisible()
    )

    # Scale/rotation/Z rows remain available (scale hidden only for lights, not puppets)
    assert insp.scale_row.isVisible()
