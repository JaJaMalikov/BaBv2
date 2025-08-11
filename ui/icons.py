from PySide6.QtGui import QPainter, QPixmap, QIcon, QColor, QPen
from PySide6.QtCore import QPointF, Qt

def make_icon(draw_fn, size: int = 32) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor('#E0E0E0'), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    draw_fn(p, size)
    p.end()
    return QIcon(pm)

def icon_plus(): return make_icon(lambda p, s: (p.drawLine(int(s/2-s*0.35), s//2, int(s/2+s*0.35), s//2), p.drawLine(s//2, int(s/2-s*0.35), s//2, int(s/2+s*0.35))))
def icon_minus(): return make_icon(lambda p, s: p.drawLine(int(s/2-s*0.35), s//2, int(s/2+s*0.35), s//2))
def icon_fit(): return make_icon(lambda p, s: (p.drawLine(4, 10, 4, 4), p.drawLine(4, 4, 10, 4), p.drawLine(s-10, 4, s-4, 4), p.drawLine(s-4, 4, s-4, 10), p.drawLine(s-4, s-10, s-4, s-4), p.drawLine(s-4, s-4, s-10, s-4), p.drawLine(10, s-4, 4, s-4), p.drawLine(4, s-4, 4, s-10)))
def icon_rotate(): return make_icon(lambda p, s: (p.drawArc(int(s*0.18), int(s*0.18), int(s*0.64), int(s*0.64), 45*16, 270*16), p.drawLine(int(s*0.5), int(s*0.18), int(s*0.5-s*0.15), int(s*0.18+s*0.15)), p.drawLine(int(s*0.5), int(s*0.18), int(s*0.5+s*0.15), int(s*0.18+s*0.15))))
def icon_chevron_left(): return make_icon(lambda p, s: p.drawPolyline([QPointF(s*0.65, s*0.2), QPointF(s*0.35, s*0.5), QPointF(s*0.65, s*0.8)]))
def icon_chevron_right(): return make_icon(lambda p, s: p.drawPolyline([QPointF(s*0.35, s*0.2), QPointF(s*0.65, s*0.5), QPointF(s*0.35, s*0.8)]))

def icon_scene_size(): return make_icon(lambda p, s: (p.drawRect(4, 4, s-8, s-8), p.drawLine(4, s-2, 8, s-2), p.drawLine(2, s-4, 2, s-8), p.drawLine(s-8, 2, s-4, 2), p.drawLine(s-2, 8, s-2, 4)))
def icon_background(): return make_icon(lambda p, s: (p.drawRect(4, 8, s-8, s-12), p.drawEllipse(8, 12, 4, 4), p.drawPolyline([QPointF(s*0.3, s*0.7), QPointF(s*0.5, s*0.5), QPointF(s*0.7, s*0.7)])))
def icon_library(): return make_icon(lambda p, s: (p.drawRect(6, 4, 4, s-8), p.drawRect(12, 4, 4, s-8)))
def icon_inspector(): return make_icon(lambda p, s: (p.drawEllipse(4, 4, s//2, s//2), p.drawLine(s//2 + 2, s//2 + 2, s-4, s-4)))
def icon_timeline(): return make_icon(lambda p, s: (p.drawRect(4, s//2 - 4, s-8, 8), p.drawLine(8, s//2 - 4, 8, s//2 + 4), p.drawLine(s-8, s//2 - 4, s-8, s//2 + 4), p.drawLine(s//2, s//2 - 4, s//2, s//2 + 4)))

def icon_onion():
    def _draw(p: QPainter, s: int):
        pen = QPen(QColor('#E0E0E0'), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        # Three layered ovals to symbolize onion skin
        p.drawEllipse(int(s*0.18), int(s*0.30), int(s*0.48), int(s*0.32))
        p.drawEllipse(int(s*0.24), int(s*0.24), int(s*0.52), int(s*0.40))
        p.drawEllipse(int(s*0.12), int(s*0.22), int(s*0.50), int(s*0.36))
    return make_icon(_draw)
