"""ui/sidebar — the NavigationView-style nav pane.

Emits ``navigate(index)`` when a section is chosen. Only Radar is live today;
the rest are disabled placeholders so the structure is visible.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from selector.ui.theme import METRICS

# (label, enabled)
_SECTIONS = (
    ("Radar", True),
    ("Combat", False),
    ("Movement", False),
    ("Settings", False),
)


class Sidebar(QWidget):
    navigate = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(METRICS.sidebar_w)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(METRICS.gap, METRICS.gutter, METRICS.gap, METRICS.gutter)
        lay.setSpacing(METRICS.gap_s)

        brand = QHBoxLayout()
        brand.setContentsMargins(METRICS.gap, 0, 0, METRICS.gutter)
        dot = QLabel("◆")
        dot.setObjectName("brandAccent")
        name = QLabel("Selector")
        name.setObjectName("brand")
        brand.addWidget(dot)
        brand.addWidget(name)
        brand.addStretch(1)
        lay.addLayout(brand)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        for i, (label, enabled) in enumerate(_SECTIONS):
            btn = QPushButton(label)
            btn.setObjectName("nav")
            btn.setCheckable(True)
            btn.setEnabled(enabled)
            if i == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda _=False, idx=i: self.navigate.emit(idx))
            self._group.addButton(btn, i)
            lay.addWidget(btn)

        lay.addStretch(1)
        hint = QLabel("v3071 · gameplay only")
        hint.setObjectName("navHint")
        lay.addWidget(hint)
