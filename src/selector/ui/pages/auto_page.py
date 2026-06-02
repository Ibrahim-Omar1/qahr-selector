"""ui/pages/auto_page — Auto-HP / Auto-Mana controls.

A pure view: two identical "pot cards" (HP, MP), each an enable toggle + a live
bar + a "drink below X%" threshold slider. Binds to ``AutoViewModel``; the cards
emit intent (enabled / threshold), the page forwards it to the view-model.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from selector.ui.theme import METRICS
from selector.viewmodels.auto_vm import AutoViewModel


class _PotCard(QFrame):
    """Enable toggle + live stat bar + threshold slider for one resource."""

    enabledChanged = Signal(bool)
    pctChanged = Signal(int)

    def __init__(self, title: str, bar_name: str, default_pct: int) -> None:
        super().__init__()
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        pad = METRICS.pad_card
        lay.setContentsMargins(pad, pad, pad, pad)
        lay.setSpacing(METRICS.gutter)

        head = QHBoxLayout()
        cap = QLabel(title.upper())
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

        self._bar = QProgressBar()
        self._bar.setObjectName(bar_name)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(12)
        self._bar.setRange(0, 100)
        lay.addWidget(self._bar)

        self._readout = QLabel("—")
        self._readout.setObjectName("monoMuted")
        lay.addWidget(self._readout)

        thr = QHBoxLayout()
        thr.setSpacing(METRICS.gap)
        lbl = QLabel("Drink below")
        lbl.setObjectName("muted")
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(5, 95)
        self._slider.setValue(default_pct)
        self._slider.valueChanged.connect(self._on_pct)
        self._thr_val = QLabel(f"{default_pct}%")
        self._thr_val.setObjectName("mono")
        self._thr_val.setFixedWidth(40)
        thr.addWidget(lbl)
        thr.addWidget(self._slider, 1)
        thr.addWidget(self._thr_val)
        lay.addLayout(thr)

    def _on_toggle(self, on: bool) -> None:
        self._toggle.setText("On" if on else "Off")
        self.enabledChanged.emit(on)

    def _on_pct(self, value: int) -> None:
        self._thr_val.setText(f"{value}%")
        self.pctChanged.emit(value)

    def update_stat(self, cur: int | None, mx: int | None, pct: int | None) -> None:
        self._bar.setValue(pct if pct is not None else 0)
        if cur is not None and mx:
            self._readout.setText(f"{cur} / {mx}" + (f"  ({pct}%)" if pct is not None else ""))
        else:
            self._readout.setText("not in world")


class AutoPage(QWidget):
    """Auto-HP / Auto-Mana page."""

    def __init__(self, vm: AutoViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = vm

        root = QVBoxLayout(self)
        root.setContentsMargins(
            METRICS.pad_page, METRICS.gutter, METRICS.pad_page, METRICS.pad_page
        )
        root.setSpacing(METRICS.gutter)

        self._hint = QLabel("Sets the game's own auto-potion thresholds — it drinks for you.")
        self._hint.setObjectName("muted")
        root.addWidget(self._hint)

        snap = vm.snapshot
        self._hp = _PotCard("Auto-HP", "hpbar", snap.hp_pct)
        self._hp.enabledChanged.connect(vm.set_hp_enabled)
        self._hp.pctChanged.connect(vm.set_hp_pct)
        root.addWidget(self._hp)

        self._mp = _PotCard("Auto-Mana", "mpbar", snap.mp_pct)
        self._mp.enabledChanged.connect(vm.set_mp_enabled)
        self._mp.pctChanged.connect(vm.set_mp_pct)
        root.addWidget(self._mp)

        root.addStretch(1)
        vm.updated.connect(self._refresh)
        self._refresh()

    def _refresh(self) -> None:
        h = self._vm.snapshot.hero
        if h is not None:
            self._hp.update_stat(h.hp, h.max_hp, h.hp_pct)
            self._mp.update_stat(h.mp, h.max_mp, h.mp_pct)
        else:
            self._hp.update_stat(None, None, None)
            self._mp.update_stat(None, None, None)
