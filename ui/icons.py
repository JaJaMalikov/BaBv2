from pathlib import Path
from PySide6.QtGui import QPainter, QPixmap, QIcon, QColor, QPen
from PySide6.QtCore import QPointF, Qt

ICONS_DIR = Path("assets/icons")

# Simple convention: place Material Symbols Rounded files as
# assets/icons/<name>.svg or .png matching our function names.

def _make_icon_from_draw(draw_fn, size: int = 32) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor('#E0E0E0'), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    draw_fn(p, size)
    p.end()
    return QIcon(pm)

def _load_icon(name: str) -> QIcon | None:
    """Load icon from assets/icons if present (prefers SVG, falls back to PNG)."""
    svg = ICONS_DIR / f"{name}.svg"
    png = ICONS_DIR / f"{name}.png"
    if svg.exists():
        return QIcon(str(svg))
    if png.exists():
        return QIcon(str(png))
    return None

def _fallbacks():
    return {
        'plus': lambda p, s: (p.drawLine(int(s/2-s*0.35), s//2, int(s/2+s*0.35), s//2), p.drawLine(s//2, int(s/2-s*0.35), s//2, int(s/2+s*0.35))),
        'minus': lambda p, s: p.drawLine(int(s/2-s*0.35), s//2, int(s/2+s*0.35), s//2),
        'fit': lambda p, s: (p.drawLine(4, 10, 4, 4), p.drawLine(4, 4, 10, 4), p.drawLine(s-10, 4, s-4, 4), p.drawLine(s-4, 4, s-4, 10), p.drawLine(s-4, s-10, s-4, s-4), p.drawLine(s-4, s-4, s-10, s-4), p.drawLine(10, s-4, 4, s-4), p.drawLine(4, s-4, 4, s-10)),
        'rotate': lambda p, s: (p.drawArc(int(s*0.18), int(s*0.18), int(s*0.64), int(s*0.64), 45*16, 270*16), p.drawLine(int(s*0.5), int(s*0.18), int(s*0.5-s*0.15), int(s*0.18+s*0.15)), p.drawLine(int(s*0.5), int(s*0.18), int(s*0.5+s*0.15), int(s*0.18+s*0.15))),
        'chevron_left': lambda p, s: p.drawPolyline([QPointF(s*0.65, s*0.2), QPointF(s*0.35, s*0.5), QPointF(s*0.65, s*0.8)]),
        'chevron_right': lambda p, s: p.drawPolyline([QPointF(s*0.35, s*0.2), QPointF(s*0.65, s*0.5), QPointF(s*0.35, s*0.8)]),
        'scene_size': lambda p, s: (p.drawRect(4, 4, s-8, s-8), p.drawLine(4, s-2, 8, s-2), p.drawLine(2, s-4, 2, s-8), p.drawLine(s-8, 2, s-4, 2), p.drawLine(s-2, 8, s-2, 4)),
        'background': lambda p, s: (p.drawRect(4, 8, s-8, s-12), p.drawEllipse(8, 12, 4, 4), p.drawPolyline([QPointF(s*0.3, s*0.7), QPointF(s*0.5, s*0.5), QPointF(s*0.7, s*0.7)])),
        'library': lambda p, s: (p.drawRect(6, 4, 4, s-8), p.drawRect(12, 4, 4, s-8)),
        'inspector': lambda p, s: (p.drawEllipse(4, 4, s//2, s//2), p.drawLine(s//2 + 2, s//2 + 2, s-4, s-4)),
        'timeline': lambda p, s: (p.drawRect(4, s//2 - 4, s-8, 8), p.drawLine(8, s//2 - 4, 8, s//2 + 4), p.drawLine(s-8, s//2 - 4, s-8, s//2 + 4), p.drawLine(s//2, s//2 - 4, s//2, s//2 + 4)),
        'onion': lambda p, s: (p.drawEllipse(int(s*0.18), int(s*0.30), int(s*0.48), int(s*0.32)), p.drawEllipse(int(s*0.24), int(s*0.24), int(s*0.52), int(s*0.40)), p.drawEllipse(int(s*0.12), int(s*0.22), int(s*0.50), int(s*0.36))),
        'save': lambda p, s: (p.drawRect(6, 6, s-12, s-12), p.drawLine(8, 10, s-8, 10), p.drawRect(10, s-14, s-20, 8)),
        'open': lambda p, s: (p.drawRect(6, 10, s-12, s-14), p.drawLine(6, 10, 12, 6), p.drawLine(12, 6, s-6, 6)),
        'delete': lambda p, s: (p.drawRect(8, 8, s-16, s-16), p.drawLine(10, 10, s-10, s-10), p.drawLine(s-10, 10, 10, s-10)),
        'duplicate': lambda p, s: (p.drawRect(8, 8, s-16, s-16), p.drawRect(12, 12, s-16, s-16)),
        'link': lambda p, s: (p.drawArc(6, s//4, s//2, s//2, 45*16, 180*16), p.drawArc(s//2-2, s//4, s//2, s//2, 225*16, 180*16)),
        'link_off': lambda p, s: (p.drawArc(6, s//4, s//2, s//2, 45*16, 180*16), p.drawArc(s//2-2, s//4, s//2, s//2, 225*16, 180*16), p.drawLine(8, s-8, s-8, 8)),
        'close': lambda p, s: (p.drawLine(8, 8, s-8, s-8), p.drawLine(8, s-8, s-8, 8)),
    }

def _icon(name: str) -> QIcon:
    ic = _load_icon(name)
    if ic is not None:
        return ic
    draw = _fallbacks().get(name)
    if draw is None:
        # Unknown name; return empty icon
        return QIcon()
    return _make_icon_from_draw(draw)

# Public helpers
def icon_plus(): return _icon('plus')
def icon_minus(): return _icon('minus')
def icon_fit(): return _icon('fit')
def icon_rotate(): return _icon('rotate')
def icon_chevron_left(): return _icon('chevron_left')
def icon_chevron_right(): return _icon('chevron_right')
def icon_scene_size(): return _icon('scene_size')
def icon_background(): return _icon('background')
def icon_library(): return _icon('library')
def icon_inspector(): return _icon('inspector')
def icon_timeline(): return _icon('timeline')
def icon_onion(): return _icon('onion')
def icon_save(): return _icon('save')
def icon_open(): return _icon('open')
def icon_delete(): return _icon('delete')
def icon_duplicate(): return _icon('duplicate')
def icon_link(): return _icon('link')
def icon_link_off(): return _icon('link_off')
def icon_close(): return _icon('close')
