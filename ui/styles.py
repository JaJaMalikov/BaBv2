import logging
from PySide6.QtGui import QFont

# This is used for the fallback icon drawing function.
ICON_COLOR = "#2D3748"

STYLE_SHEET = """
/* GLOBAL SETTINGS */
* {
    color: #1A202C; /* Default dark text */
    font-family: Poppins, sans-serif;
}

/* MAIN WINDOW & VIEW */
QMainWindow, QDialog {
    background-color: #E2E8F0; /* Light grey background */
}

QGraphicsView {
    border: none;
}

/* PANELS & DOCKS (Library, Inspector, Timeline) */
DraggableOverlay, PanelOverlay {
    background-color: rgba(247, 248, 252, 0.9); /* Semi-transparent white */
    border-radius: 12px;
    border: 1px solid #D0D5DD;
}

DraggableHeader {
    background-color: rgba(237, 242, 247, 0.9);
    border-bottom: 1px solid rgba(203, 213, 224, 0.5);
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

DraggableHeader {
    background-color: rgba(0, 0, 0, 0.05);
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

DraggableHeader QLabel {
    font-weight: bold;
    color: #2D3748;
}


/* TOOL BUTTONS & ICONS */
QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 5px;
}

QToolButton:hover {
    background-color: #E3E6FD; /* Lavender hover */
}

QToolButton:checked {
    background-color: #E53E3E; /* Red background when active */
}


/* WIDGETS (Inputs, Lists, etc.) */
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {
    background-color: #EDF2F7;
    border: 1px solid #CBD5E0;
    border-radius: 4px;
    padding: 4px;
    color: #1A202C;
}

QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #E53E3E;
    background-color: white;
}

QTreeView, QListWidget {
    background-color: transparent;
    border: none;
}

QTreeView::item, QListWidget::item {
    padding: 4px;
    border-radius: 4px;
}

QTreeView::item:hover, QListWidget::item:hover {
    background-color: #E2E8F0;
}

QTreeView::item:selected, QListWidget::item:selected {
    background-color: #E53E3E;
    color: white;
}

QScrollArea {
    border: none;
}

/* TIMELINE */
TimelineWidget {
    background-color: #2D3748;
    color: #E2E8F0;
}

TimelineWidget QToolButton {
    background-color: transparent;
    color: #E2E8F0;
}

TimelineWidget QToolButton:hover {
    background-color: #4A5568;
}

TimelineWidget QToolButton:checked {
    background-color: #E53E3E;
    color: white;
}

"""

def apply_stylesheet(app):
    """Apply the application's stylesheet."""
    app.setStyleSheet(STYLE_SHEET)
    try:
        app.setFont(QFont("Poppins", 10))
    except RuntimeError:
        logging.warning("Poppins font not found, using system default.")
