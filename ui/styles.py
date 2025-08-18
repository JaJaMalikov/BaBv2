"""Module for managing application styles and themes."""

import logging
from typing import Any
from PySide6.QtGui import QFont
from .ui_profile import UIProfile

# This is used for the fallback icon drawing function.
ICON_COLOR = "#2D3748"


def build_stylesheet(params: dict) -> str:
    """Generate a Qt stylesheet from simple, human-friendly parameters.

    Expected keys (hex or rgba strings where appropriate):
    - bg_color, text_color
    - panel_bg (without opacity), panel_opacity (0..1), panel_border
    - accent_color, hover_color
    - group_title_color
    - radius (int px), font_size (int pt)
    - tooltip_bg (hex), tooltip_text (hex), tooltip_border (optional hex)
    - font_family (string)
    - input_bg, input_border, input_text, input_focus_bg, input_focus_border
    - list_hover_bg, list_selected_bg, list_selected_text
    - checkbox_unchecked_bg, checkbox_unchecked_border
    - checkbox_checked_bg, checkbox_checked_border, checkbox_checked_hover
    """

    def rgba(hex_color: str, alpha: float) -> str:
        hex_color = hex_color.strip()
        if hex_color.startswith("#") and len(hex_color) in (7, 9):
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            a = max(0, min(255, int(alpha * 255)))
            return f"rgba({r},{g},{b},{a})"
        return hex_color

    bg = params.get("bg_color", "#E2E8F0")
    text = params.get("text_color", "#1A202C")
    panel = params.get("panel_bg", "#F7F8FC")
    panel_op = float(params.get("panel_opacity", 0.9))
    border = params.get("panel_border", "#D0D5DD")
    accent = params.get("accent_color", "#E53E3E")
    hover = params.get("hover_color", "#E3E6FD")
    group = params.get("group_title_color", "#2D3748")
    radius = int(params.get("radius", 12))
    fsize = int(params.get("font_size", 10))
    # Inputs and lists
    in_bg = params.get("input_bg", "#EDF2F7")
    in_border = params.get("input_border", "#CBD5E0")
    in_text = params.get("input_text", text)
    in_focus_bg = params.get("input_focus_bg", "#FFFFFF")
    in_focus_border = params.get("input_focus_border", accent)
    list_hover = params.get("list_hover_bg", "#E2E8F0")
    list_sel_bg = params.get("list_selected_bg", accent)
    list_sel_text = params.get("list_selected_text", "#FFFFFF")
    # Checkboxes
    cb_un_bg = params.get("checkbox_unchecked_bg", "#EDF2F7")
    cb_un_border = params.get("checkbox_unchecked_border", "#A0AEC0")
    cb_ch_bg = params.get("checkbox_checked_bg", accent)
    cb_ch_border = params.get("checkbox_checked_border", "#C53030")
    cb_ch_hover = params.get("checkbox_checked_hover", "#F56565")

    panel_rgba = rgba(panel, panel_op)
    header_bg = params.get("header_bg")
    header_text = params.get("header_text", text)
    header_border = params.get("header_border", border)
    if header_bg:
        header_rgba = rgba(header_bg, 1.0)
    else:
        header_rgba = rgba("#EDF2F7", min(1.0, panel_op + 0.05))
    border_rgba = rgba(border, min(1.0, panel_op))
    tip_bg = params.get("tooltip_bg", panel)
    tip_text = params.get("tooltip_text", text)
    tip_border = params.get("tooltip_border", border)
    family = params.get("font_family", "Poppins")

    return f"""
* {{ color: {text}; font-family: {family}, sans-serif; font-size: {fsize}pt; }}
QMainWindow, QDialog {{ background-color: {bg}; }}
DraggableOverlay, PanelOverlay {{ background-color: {panel_rgba}; border-radius: {radius}px; border: 1px solid {border_rgba}; }}
DraggableHeader {{ background-color: {header_rgba}; border-bottom: 1px solid {rgba(header_border, 0.5)}; border-top-left-radius: {radius}px; border-top-right-radius: {radius}px; }}
DraggableHeader QLabel {{ color: {header_text}; font-weight: bold; }}
QToolButton {{ background: transparent; border: none; border-radius: 6px; padding: 5px; }}
QToolButton:hover {{ background-color: {hover}; }}
    QToolButton:checked {{ background-color: {accent}; color: white; }}
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{ background-color: {in_bg}; border: 1px solid {in_border}; border-radius: 4px; padding: 4px; color: {in_text}; }}
    QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {in_focus_border}; background-color: {in_focus_bg}; }}
    QTreeView, QListWidget {{ background: transparent; border: none; }}
    QTreeView::item, QListWidget::item {{ padding: 4px; border-radius: 4px; }}
    QTreeView::item:hover, QListWidget::item:hover {{ background-color: {list_hover}; }}
    QTreeView::item:selected, QListWidget::item:selected {{ background-color: {list_sel_bg}; color: {list_sel_text}; }}
    QCheckBox {{ spacing: 6px; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 3px; }}
    QCheckBox::indicator:unchecked {{ background-color: {cb_un_bg}; border: 1px solid {cb_un_border}; }}
    QCheckBox::indicator:unchecked:hover {{ background-color: {list_hover}; }}
    QCheckBox::indicator:checked {{ background-color: {cb_ch_bg}; border: 1px solid {cb_ch_border}; }}
    QCheckBox::indicator:checked:hover {{ background-color: {cb_ch_hover}; }}
QGroupBox {{ font-weight: 600; color: {group}; margin-top: 8px; }}
QGroupBox:title {{ subcontrol-origin: margin; left: 6px; padding: 2px 4px; }}
TimelineWidget {{ background-color: #2D3748; color: #E2E8F0; }}
TimelineWidget QToolButton {{ background: transparent; color: #E2E8F0; }}
TimelineWidget QToolButton:hover {{ background-color: #4A5568; }}
TimelineWidget QToolButton:checked {{ background-color: {accent}; color: white; }}
QToolTip {{ background-color: {tip_bg}; color: {tip_text}; border: 1px solid {tip_border}; border-radius: 6px; padding: 4px 8px; }}
"""


def apply_stylesheet(app, profile: UIProfile | None = None) -> None:
    """Apply the application's stylesheet based on the given profile."""
    try:
        profile = profile or UIProfile.from_qsettings()
        css = build_stylesheet(profile.theme.custom_params)
        app.setStyleSheet(css)
        try:
            app.setFont(QFont(str(profile.theme.font_family or "Poppins"), 10))
        except RuntimeError:
            logging.warning("Requested font not found, using system default.")
    except Exception:
        logging.exception("Failed to apply theme from settings")
