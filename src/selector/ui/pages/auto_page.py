"""ui/pages/auto_page — Auto-HP (minimal).

One small card: an enable toggle + a "drink below X%" slider. It writes the
game's native auto-HP-pot settings via ``AutoController``; the game does the
drinking, so there's nothing to poll or display live.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from selector.ui.theme import METRICS
from selector.viewmodels.auto_vm import AutoController


class AutoPage(QWidget):
    def __init__(self, controller: AutoController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._c = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(
            METRICS.pad_page, METRICS.gutter, METRICS.pad_page, METRICS.pad_page
        )
        root.setSpacing(METRICS.gutter)

        card = QFrame()
        card.setObjectName("card")
        card.setMaximumWidth(440)
        lay = QVBoxLayout(card)
        pad = METRICS.pad_card
        lay.setContentsMargins(pad, pad, pad, pad)
        lay.setSpacing(METRICS.gutter)

        head = QHBoxLayout()
        cap = QLabel("AUTO-HP")
        cap.setObjectName("cardTitle")
        self._toggle = QPushButton("Off")
        self._toggle.setObjectName("toggle")
        self._toggle.setCheckable(True)
        self._toggle.setFixedHeight(METRICS.ctl_h)
        self._toggle.setFixedWidth(64)
        self._toggle.toggled.connect(self._on_toggle)
        head.addWidget(cap)
        head.addStretch(1)
        head.addWidget(self._toggle)
        lay.addLayout(head)

        thr = QHBoxLayout()
        thr.setSpacing(METRICS.gap)
        lbl = QLabel("Drink below")
        lbl.setObjectName("muted")
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(5, 95)
        self._slider.setValue(controller.pct)
        self._slider.valueChanged.connect(self._on_pct)
        self._val = QLabel(f"{controller.pct}%")
        self._val.setObjectName("mono")
        self._val.setFixedWidth(40)
        thr.addWidget(lbl)
        thr.addWidget(self._slider, 1)
        thr.addWidget(self._val)
        lay.addLayout(thr)

        self._status = QLabel("Off")
        self._status.setObjectName("muted")
        lay.addWidget(self._status)

        root.addWidget(card)
        root.addStretch(1)

    def _on_toggle(self, on: bool) -> None:
        self._toggle.setText("On" if on else "Off")
        self._set_status(on, self._c.set_enabled(on))

    def _on_pct(self, value: int) -> None:
        self._val.setText(f"{value}%")
        self._set_status(self._c.enabled, self._c.set_pct(value))

    def _set_status(self, on: bool, applied: bool) -> None:
        if not on:
            self._status.setText("Off")
        elif applied:
            self._status.setText(f"On — game drinks an HP potion below {self._c.pct}%")
        else:
            self._status.setText("On — couldn't apply (game not attached?)")
