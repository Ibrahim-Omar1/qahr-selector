"""ui/sidebar — collapsible NavigationView-style nav pane.

A hamburger toggles between expanded (icon + label) and collapsed (icon only,
with tooltips). Emits ``navigate(index)`` when a section is chosen. Only Radar is
live today; the rest are disabled placeholders.
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from selector.ui.icons import COMBAT, MOVEMENT, NAV_MENU, RADAR, SETTINGS, glyph_icon
from selector.ui.theme import COLORS, METRICS

# (label, icon codepoint, enabled)
_SECTIONS = (
    ("Radar", RADAR, True),
    ("Combat", COMBAT, False),
    ("Movement", MOVEMENT, False),
    ("Settings", SETTINGS, False),
)


class Sidebar(QWidget):
    navigate = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._collapsed = False
        self.setFixedWidth(METRICS.sidebar_w)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(METRICS.gap, METRICS.gutter, METRICS.gap, METRICS.gutter)
        lay.setSpacing(METRICS.gap_s)

        lay.addLayout(self._build_top())
        lay.addSpacing(METRICS.gap)

        self._buttons: list[QPushButton] = []
        self._labels: list[str] = []
        group = QButtonGroup(self)
        group.setExclusive(True)
        for i, (label, icon_cp, enabled) in enumerate(_SECTIONS):
            btn = QPushButton(label)
            btn.setObjectName("nav")
            btn.setCheckable(True)
            btn.setEnabled(enabled)
            btn.setToolTip(label)
            btn.setIcon(glyph_icon(icon_cp, COLORS.icon))
            btn.setIconSize(QSize(18, 18))
            if i == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda _=False, idx=i: self.navigate.emit(idx))
            group.addButton(btn, i)
            lay.addWidget(btn)
            self._buttons.append(btn)
            self._labels.append(label)

        lay.addStretch(1)
        self._hint = QLabel("v3071 · gameplay only")
        self._hint.setObjectName("navHint")
        lay.addWidget(self._hint)

    def _build_top(self) -> QHBoxLayout:
        top = QHBoxLayout()
        top.setContentsMargins(METRICS.gap_s, 0, 0, 0)
        top.setSpacing(METRICS.gap)

        self._burger = QPushButton()
        self._burger.setObjectName("hamburger")
        self._burger.setIcon(glyph_icon(NAV_MENU, COLORS.icon, 16))
        self._burger.setIconSize(QSize(16, 16))
        self._burger.setToolTip("Collapse / expand")
        self._burger.clicked.connect(self.toggle)
        top.addWidget(self._burger)

        self._dot = QLabel("◆")
        self._dot.setObjectName("brandAccent")
        self._brand = QLabel("Selector")
        self._brand.setObjectName("brand")
        top.addWidget(self._dot)
        top.addWidget(self._brand)
        top.addStretch(1)
        return top

    def toggle(self) -> None:
        self._collapsed = not self._collapsed
        self.setFixedWidth(
            METRICS.sidebar_w_collapsed if self._collapsed else METRICS.sidebar_w
        )
        self._dot.setVisible(not self._collapsed)
        self._brand.setVisible(not self._collapsed)
        self._hint.setVisible(not self._collapsed)
        for btn, label in zip(self._buttons, self._labels, strict=True):
            btn.setText("" if self._collapsed else label)
            btn.setProperty("collapsed", self._collapsed)
            style = btn.style()
            style.unpolish(btn)
            style.polish(btn)
