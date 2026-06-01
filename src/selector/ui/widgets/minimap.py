"""ui/widgets/minimap — hero-centered radar canvas (custom-painted).

Plots nearby entities by their tile offset from the hero, with range rings and
a N/E/S/W crosshair. Colors come from ``ui.theme.kind_color`` so the minimap and
the table stay visually consistent. Render-only: it draws whatever snapshot it's
given and never reads the engine itself.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from selector.core.models import Entity, EntityKind, Hero
from selector.ui.theme import COLORS, kind_color


class MinimapView(QWidget):
    """A square radar; call :meth:`set_data` each frame, then it repaints."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(260, 260)
        self._hero: Hero | None = None
        self._entities: list[Entity] = []
        self._radius: int = 32

    def set_data(self, hero: Hero | None, entities: list[Entity], radius: int) -> None:
        self._hero, self._entities, self._radius = hero, entities, max(1, radius)
        self.update()

    # --- painting -------------------------------------------------------------
    def paintEvent(self, event: object) -> None:  # noqa: N802 (Qt override)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        side = min(w, h)
        cx, cy = w / 2.0, h / 2.0
        margin = 16.0
        plot_r = side / 2.0 - margin
        scale = plot_r / self._radius  # px per tile

        self._draw_grid(p, cx, cy, plot_r)
        if self._hero is None:
            self._draw_centered_text(p, cx, cy, "no hero")
            p.end()
            return
        self._draw_entities(p, cx, cy, scale, plot_r)
        self._draw_hero(p, cx, cy)
        p.end()

    def _draw_grid(self, p: QPainter, cx: float, cy: float, plot_r: float) -> None:
        ring = QPen(QColor(255, 255, 255, 26), 1.0)
        p.setPen(ring)
        for frac in (0.5, 1.0):
            r = plot_r * frac
            p.drawEllipse(QPointF(cx, cy), r, r)
        # crosshair
        p.setPen(QPen(QColor(255, 255, 255, 18), 1.0))
        p.drawLine(QPointF(cx - plot_r, cy), QPointF(cx + plot_r, cy))
        p.drawLine(QPointF(cx, cy - plot_r), QPointF(cx, cy + plot_r))
        # cardinal labels
        f = QFont()
        f.setPointSize(8)
        p.setFont(f)
        p.setPen(QColor("#7A7A7A"))
        p.drawText(int(cx - 4), int(cy - plot_r - 4), "N")
        p.drawText(int(cx - 4), int(cy + plot_r + 12), "S")
        p.drawText(int(cx + plot_r + 4), int(cy + 4), "E")
        p.drawText(int(cx - plot_r - 12), int(cy + 4), "W")

    def _draw_entities(
        self, p: QPainter, cx: float, cy: float, scale: float, plot_r: float
    ) -> None:
        hero = self._hero
        assert hero is not None
        for e in self._entities:
            ex = cx + (e.x - hero.x) * scale
            ey = cy + (e.y - hero.y) * scale
            # clamp to the plot circle edge if slightly outside
            dot = 5.0 if e.kind in (EntityKind.PLAYER, EntityKind.TARGET) else 4.0
            color = QColor(kind_color(e.kind))
            if e.kind is EntityKind.TARGET:
                p.setPen(QPen(color, 1.5))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(ex, ey), dot + 3, dot + 3)
            p.setPen(QPen(QColor(0, 0, 0, 90), 1.0))
            p.setBrush(color)
            p.drawEllipse(QPointF(ex, ey), dot, dot)

    def _draw_hero(self, p: QPainter, cx: float, cy: float) -> None:
        accent = QColor(COLORS.accent)
        halo = QColor(accent)
        halo.setAlpha(60)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(halo)
        p.drawEllipse(QPointF(cx, cy), 9, 9)
        p.setPen(QPen(QColor("#0B0E14"), 1.5))
        p.setBrush(accent)
        p.drawEllipse(QPointF(cx, cy), 4.5, 4.5)

    def _draw_centered_text(self, p: QPainter, cx: float, cy: float, text: str) -> None:
        p.setPen(QColor("#7A7A7A"))
        p.drawText(int(cx - 28), int(cy + 4), text)
