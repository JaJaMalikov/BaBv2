"""Module for managing application styles and themes."""

import logging
from PySide6.QtGui import QFont

# This is used for the fallback icon drawing function.
ICON_COLOR = "#2D3748"

STYLE_SHEET_LIGHT = """
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

/* CHECKBOXES: Improve contrast and checked visibility */
QCheckBox {
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 3px;
}
QCheckBox::indicator:unchecked {
    background-color: #EDF2F7;
    border: 1px solid #A0AEC0;
}
QCheckBox::indicator:unchecked:hover {
    background-color: #E2E8F0;
}
QCheckBox::indicator:checked {
    background-color: #E53E3E; /* Accent */
    border: 1px solid #C53030;
}
QCheckBox::indicator:checked:hover {
    background-color: #F56565;
}

/* GROUP BOX TITLES */
QGroupBox {
    font-weight: 600;
    color: #2D3748;
    margin-top: 8px;
}
QGroupBox:title {
    subcontrol-origin: margin;
    left: 6px;
    padding: 2px 4px;
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

STYLE_SHEET_DARK = """
* { color: #E2E8F0; font-family: Poppins, sans-serif; }
QMainWindow, QDialog { background-color: #1F2937; }
DraggableOverlay, PanelOverlay { background-color: rgba(31,41,55,0.92); border-radius: 12px; border: 1px solid #374151; }
DraggableHeader { background-color: rgba(55,65,81,0.9); border-bottom: 1px solid rgba(75,85,99,0.6); border-top-left-radius: 12px; border-top-right-radius: 12px; }
QToolButton { background: transparent; border: none; border-radius: 6px; padding: 5px; }
QToolButton:hover { background-color: #374151; }
QToolButton:checked { background-color: #EF4444; }
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox { background-color: #111827; border: 1px solid #374151; border-radius: 4px; padding: 4px; color: #E5E7EB; }
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus { border-color: #EF4444; background-color: #0B0F16; }
QTreeView, QListWidget { background-color: transparent; border: none; }
QTreeView::item, QListWidget::item { padding: 4px; border-radius: 4px; }
QTreeView::item:hover, QListWidget::item:hover { background-color: #374151; }
QTreeView::item:selected, QListWidget::item:selected { background-color: #EF4444; color: white; }
QCheckBox { spacing: 6px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 3px; }
QCheckBox::indicator:unchecked { background-color: #111827; border: 1px solid #4B5563; }
QCheckBox::indicator:unchecked:hover { background-color: #0B0F16; }
QCheckBox::indicator:checked { background-color: #EF4444; border: 1px solid #B91C1C; }
QCheckBox::indicator:checked:hover { background-color: #F87171; }
QGroupBox { font-weight: 600; color: #E5E7EB; margin-top: 8px; }
QGroupBox:title { subcontrol-origin: margin; left: 6px; padding: 2px 4px; }
TimelineWidget { background-color: #111827; color: #D1D5DB; }
TimelineWidget QToolButton { background: transparent; color: #D1D5DB; }
TimelineWidget QToolButton:hover { background-color: #1F2937; }
TimelineWidget QToolButton:checked { background-color: #EF4444; color: white; }
"""

def build_stylesheet(params: dict) -> str:
    """Generate a Qt stylesheet from simple, human-friendly parameters.

    Expected keys (hex or rgba strings where appropriate):
    - bg_color, text_color
    - panel_bg (without opacity), panel_opacity (0..1), panel_border
    - accent_color, hover_color
    - group_title_color
    - radius (int px), font_size (int pt)
    """
    def rgba(hex_color: str, alpha: float) -> str:
        hex_color = hex_color.strip()
        if hex_color.startswith('#') and len(hex_color) in (7, 9):
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            a = max(0, min(255, int(alpha * 255)))
            return f"rgba({r},{g},{b},{a})"
        return hex_color

    bg = params.get('bg_color', '#E2E8F0')
    text = params.get('text_color', '#1A202C')
    panel = params.get('panel_bg', '#F7F8FC')
    panel_op = float(params.get('panel_opacity', 0.9))
    border = params.get('panel_border', '#D0D5DD')
    accent = params.get('accent_color', '#E53E3E')
    hover = params.get('hover_color', '#E3E6FD')
    group = params.get('group_title_color', '#2D3748')
    radius = int(params.get('radius', 12))
    fsize = int(params.get('font_size', 10))

    panel_rgba = rgba(panel, panel_op)
    header_rgba = rgba('#EDF2F7', min(1.0, panel_op + 0.05))
    border_rgba = rgba(border, min(1.0, panel_op))

    return f"""
* {{ color: {text}; font-family: Poppins, sans-serif; font-size: {fsize}pt; }}
QMainWindow, QDialog {{ background-color: {bg}; }}
DraggableOverlay, PanelOverlay {{ background-color: {panel_rgba}; border-radius: {radius}px; border: 1px solid {border_rgba}; }}
DraggableHeader {{ background-color: {header_rgba}; border-bottom: 1px solid {rgba(border, 0.5)}; border-top-left-radius: {radius}px; border-top-right-radius: {radius}px; }}
QToolButton {{ background: transparent; border: none; border-radius: 6px; padding: 5px; }}
QToolButton:hover {{ background-color: {hover}; }}
QToolButton:checked {{ background-color: {accent}; color: white; }}
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{ background-color: #EDF2F7; border: 1px solid #CBD5E0; border-radius: 4px; padding: 4px; color: {text}; }}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {accent}; background-color: white; }}
QTreeView, QListWidget {{ background: transparent; border: none; }}
QTreeView::item, QListWidget::item {{ padding: 4px; border-radius: 4px; }}
QTreeView::item:hover, QListWidget::item:hover {{ background-color: #E2E8F0; }}
QTreeView::item:selected, QListWidget::item:selected {{ background-color: {accent}; color: white; }}
QCheckBox {{ spacing: 6px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 3px; }}
QCheckBox::indicator:unchecked {{ background-color: #EDF2F7; border: 1px solid #A0AEC0; }}
QCheckBox::indicator:unchecked:hover {{ background-color: #E2E8F0; }}
QCheckBox::indicator:checked {{ background-color: {accent}; border: 1px solid #C53030; }}
QCheckBox::indicator:checked:hover {{ background-color: #F56565; }}
QGroupBox {{ font-weight: 600; color: {group}; margin-top: 8px; }}
QGroupBox:title {{ subcontrol-origin: margin; left: 6px; padding: 2px 4px; }}
TimelineWidget {{ background-color: #2D3748; color: #E2E8F0; }}
TimelineWidget QToolButton {{ background: transparent; color: #E2E8F0; }}
TimelineWidget QToolButton:hover {{ background-color: #4A5568; }}
TimelineWidget QToolButton:checked {{ background-color: {accent}; color: white; }}
"""
def apply_stylesheet(app):
    """Apply the application's stylesheet.

    Reads QSettings 'ui/theme' to select light/dark theme.
    """
    try:
        from PySide6.QtCore import QSettings
        import ui.icons as app_icons
        s = QSettings("JaJa", "Macronotron")
        theme = str(s.value("ui/theme", "dark")).lower()
        # Ensure icon colors follow the selected theme
        app_icons.load_colors_from_settings()
        if theme == "custom":
            custom_css = s.value("ui/custom_stylesheet")
            if custom_css:
                app.setStyleSheet(custom_css)
                try:
                    app.setFont(QFont("Poppins", 10))
                except RuntimeError:
                    logging.warning("Poppins font not found, using system default.")
                return
    except Exception:
        theme = "dark"
    css = STYLE_SHEET_DARK if theme == "dark" else STYLE_SHEET_LIGHT
    app.setStyleSheet(css)
    try:
        app.setFont(QFont("Poppins", 10))
    except RuntimeError:
        logging.warning("Poppins font not found, using system default.")
