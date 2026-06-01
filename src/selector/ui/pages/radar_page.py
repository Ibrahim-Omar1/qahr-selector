"""ui/pages/radar_page — the ESP/radar page (minimap + table).

A pure view: binds to ``RadarViewModel.updated`` and renders the latest
snapshot. No engine access here.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from selector.ui.theme import METRICS
from selector.ui.widgets.entity_table import EntityTable, EntityTableModel
from selector.ui.widgets.minimap import MinimapView
from selector.viewmodels.radar_vm import RadarViewModel


def _card(title: str, body: QWidget) -> QFrame:
    """Wrap a widget in a titled Fluent card."""
    frame = QFrame()
    frame.setObjectName("card")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(METRICS.pad_l, METRICS.pad, METRICS.pad_l, METRICS.pad_l)
    lay.setSpacing(METRICS.pad)
    cap = QLabel(title.upper())
    cap.setObjectName("cardTitle")
    lay.addWidget(cap)
    lay.addWidget(body)
    return frame


class RadarPage(QWidget):
    """ESP radar: a hero/status strip, a minimap, and an entity table."""

    def __init__(self, vm: RadarViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = vm
        self._minimap = MinimapView()
        self._model = EntityTableModel(self)
        self._table = EntityTable(self._model)

        root = QVBoxLayout(self)
        root.setContentsMargins(METRICS.pad_xl, METRICS.pad_l, METRICS.pad_xl, METRICS.pad_xl)
        root.setSpacing(METRICS.pad_l)
        root.addLayout(self._build_strip())

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(_card("Minimap", self._minimap))
        split.addWidget(_card("Entities", self._table))
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 4)
        split.setHandleWidth(METRICS.pad_l)
        root.addWidget(split, 1)

        vm.updated.connect(self._refresh)
        self._refresh()

    def _build_strip(self) -> QHBoxLayout:
        strip = QHBoxLayout()
        strip.setSpacing(METRICS.pad_l)
        self._hero_lbl = QLabel("—")
        self._hero_lbl.setObjectName("mono")
        self._count_lbl = QLabel("0 entities")
        self._count_lbl.setObjectName("pill")
        strip.addWidget(self._hero_lbl)
        strip.addStretch(1)
        strip.addWidget(self._count_lbl)

        rng = QLabel("Range")
        rng.setObjectName("muted")
        self._radius = QSlider(Qt.Orientation.Horizontal)
        self._radius.setRange(8, 96)
        self._radius.setValue(self._vm.snapshot.radius)
        self._radius.setFixedWidth(140)
        self._radius_val = QLabel(f"{self._vm.snapshot.radius}")
        self._radius_val.setObjectName("mono")
        self._radius.valueChanged.connect(self._on_radius)
        strip.addWidget(rng)
        strip.addWidget(self._radius)
        strip.addWidget(self._radius_val)
        return strip

    def _on_radius(self, value: int) -> None:
        self._vm.set_radius(value)
        self._radius_val.setText(str(value))

    def _refresh(self) -> None:
        snap = self._vm.snapshot
        if snap.hero is not None:
            h = snap.hero
            self._hero_lbl.setText(f"{h.name or '—'}   ({h.x}, {h.y})   {h.pk_name or ''}")
        else:
            self._hero_lbl.setText("not in world")
        self._count_lbl.setText(f"{len(snap.entities)} entities")
        self._minimap.set_data(snap.hero, snap.entities, snap.radius)
        self._model.set_entities(snap.entities)
