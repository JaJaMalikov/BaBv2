from functools import lru_cache

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

@lru_cache()
def icon_plus() -> QIcon:
    return make_icon(
        lambda p, s: (
            p.drawLine(int(s/2 - s * 0.35), s // 2, int(s/2 + s * 0.35), s // 2),
            p.drawLine(s // 2, int(s/2 - s * 0.35), s // 2, int(s/2 + s * 0.35)),
        )
    )
@lru_cache()
def icon_minus() -> QIcon:
    return make_icon(lambda p, s: p.drawLine(int(s / 2 - s * 0.35), s // 2, int(s / 2 + s * 0.35), s // 2))
@lru_cache()
def icon_fit() -> QIcon:
    return make_icon(
        lambda p, s: (
            p.drawLine(4, 10, 4, 4),
            p.drawLine(4, 4, 10, 4),
            p.drawLine(s - 10, 4, s - 4, 4),
            p.drawLine(s - 4, 4, s - 4, 10),
            p.drawLine(s - 4, s - 10, s - 4, s - 4),
            p.drawLine(s - 4, s - 4, s - 10, s - 4),
            p.drawLine(10, s - 4, 4, s - 4),
            p.drawLine(4, s - 4, 4, s - 10),
        )
    )
@lru_cache()
def icon_rotate() -> QIcon:
    return make_icon(
        lambda p, s: (
            p.drawArc(int(s * 0.18), int(s * 0.18), int(s * 0.64), int(s * 0.64), 45 * 16, 270 * 16),
            p.drawLine(int(s * 0.5), int(s * 0.18), int(s * 0.5 - s * 0.15), int(s * 0.18 + s * 0.15)),
            p.drawLine(int(s * 0.5), int(s * 0.18), int(s * 0.5 + s * 0.15), int(s * 0.18 + s * 0.15)),
        )
    )
@lru_cache()
def icon_chevron_left() -> QIcon:
    return make_icon(
        lambda p, s: p.drawPolyline([QPointF(s * 0.65, s * 0.2), QPointF(s * 0.35, s * 0.5), QPointF(s * 0.65, s * 0.8)])
    )

@lru_cache()
def icon_chevron_right() -> QIcon:
    return make_icon(
        lambda p, s: p.drawPolyline([QPointF(s * 0.35, s * 0.2), QPointF(s * 0.65, s * 0.5), QPointF(s * 0.35, s * 0.8)])
    )

@lru_cache()
def icon_scene_size() -> QIcon:
    return make_icon(
        lambda p, s: (
            p.drawRect(4, 4, s - 8, s - 8),
            p.drawLine(4, s - 2, 8, s - 2),
            p.drawLine(2, s - 4, 2, s - 8),
            p.drawLine(s - 8, 2, s - 4, 2),
            p.drawLine(s - 2, 8, s - 2, 4),
        )
    )

@lru_cache()
def icon_background() -> QIcon:
    return make_icon(
        lambda p, s: (
            p.drawRect(4, 8, s - 8, s - 12),
            p.drawEllipse(8, 12, 4, 4),
            p.drawPolyline([QPointF(s * 0.3, s * 0.7), QPointF(s * 0.5, s * 0.5), QPointF(s * 0.7, s * 0.7)]),
        )
    )

@lru_cache()
def icon_library() -> QIcon:
    return make_icon(lambda p, s: (p.drawRect(6, 4, 4, s - 8), p.drawRect(12, 4, 4, s - 8)))

@lru_cache()
def icon_inspector() -> QIcon:
    return make_icon(
        lambda p, s: (p.drawEllipse(4, 4, s // 2, s // 2), p.drawLine(s // 2 + 2, s // 2 + 2, s - 4, s - 4))
    )

@lru_cache()
def icon_timeline() -> QIcon:
    return make_icon(
        lambda p, s: (
            p.drawRect(4, s // 2 - 4, s - 8, 8),
            p.drawLine(8, s // 2 - 4, 8, s // 2 + 4),
            p.drawLine(s - 8, s // 2 - 4, s - 8, s // 2 + 4),
            p.drawLine(s // 2, s // 2 - 4, s // 2, s // 2 + 4),
        )
    )

@lru_cache()
def icon_onion() -> QIcon:
    def _draw(p: QPainter, s: int) -> None:
        pen = QPen(QColor('#E0E0E0'), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        # Three layered ovals to symbolize onion skin
        p.drawEllipse(int(s * 0.18), int(s * 0.30), int(s * 0.48), int(s * 0.32))
        p.drawEllipse(int(s * 0.24), int(s * 0.24), int(s * 0.52), int(s * 0.40))
        p.drawEllipse(int(s * 0.12), int(s * 0.22), int(s * 0.50), int(s * 0.36))
    return make_icon(_draw)
