ACCENT_RED = "#E53935"
ACCENT_RED_RGBA = "229,57,53"

BUTTON_STYLE = """
    QToolButton {
        background-color: transparent;
        border: 1px solid transparent;
        padding: 2px;
        color: #E0E0E0;
        border-radius: 8px;
    }
    QToolButton:hover {
        background-color: rgba(255,255,255,0.08);
        border-color: rgba(255,255,255,0.15);
    }
    QToolButton:checked {
        background-color: rgba(255,255,255,0.14);
        border-color: rgba(255,255,255,0.22);
    }
    QToolButton:focus {
        outline: none;
        border-color: rgba(255,255,255,0.35);
    }
"""
