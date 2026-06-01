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
    """Wrap a widget in a titled Fluent card (even padding all round)."""
    frame = QFrame()
    frame.setObjectName("card")
    lay = QVBoxLayout(frame)
    pad = METRICS.pad_card
    lay.setContentsMargins(pad, pad, pad, pad)
    lay.setSpacing(METRICS.gutter)
    cap = QLabel(title.upper())
    cap.setObjectName("cardTitle")
    lay.addWidget(cap)
    lay.addWidget(body, 1)
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
        root.setContentsMargins(
            METRICS.pad_page, METRICS.gutter, METRICS.pad_page, METRICS.pad_page
        )
        root.setSpacing(METRICS.gutter)
        root.addLayout(self._build_strip())

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(_card("Minimap", self._minimap))
        split.addWidget(_card("Entities", self._table))
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 4)
        split.setHandleWidth(METRICS.gutter)
        root.addWidget(split, 1)

        vm.updated.connect(self._refresh)
        self._refresh()

    def _build_strip(self) -> QHBoxLayout:
        v = Qt.AlignmentFlag.AlignVCenter
        strip = QHBoxLayout()
        strip.setSpacing(METRICS.gutter)

        self._hero_lbl = QLabel("—")              # name + coords, default UI font
        strip.addWidget(self._hero_lbl, 0, v)
        strip.addStretch(1)

        self._count_lbl = QLabel("0 entities")
        self._count_lbl.setObjectName("muted")
        strip.addWidget(self._count_lbl, 0, v)

        rng = QLabel("Range")
        rng.setObjectName("muted")
        self._radius = QSlider(Qt.Orientation.Horizontal)
        self._radius.setRange(8, 96)
        self._radius.setValue(self._vm.snapshot.radius)
        self._radius.setFixedWidth(160)
        self._radius_val = QLabel(f"{self._vm.snapshot.radius}")
        self._radius_val.setObjectName("monoMuted")
        self._radius_val.setFixedWidth(22)
        self._radius.valueChanged.connect(self._on_radius)
        strip.addWidget(rng, 0, v)
        strip.addWidget(self._radius, 0, v)
        strip.addWidget(self._radius_val, 0, v)
        return strip

    def _on_radius(self, value: int) -> None:
        self._vm.set_radius(value)
        self._radius_val.setText(str(value))

    def _refresh(self) -> None:
        snap = self._vm.snapshot
        if snap.hero is not None:
            h = snap.hero
            parts = [h.name or "—", f"({h.x}, {h.y})"]
            if h.pk_name:
                parts.append(h.pk_name)
            self._hero_lbl.setText("   ·   ".join(parts))
        else:
            self._hero_lbl.setText("not in world")
        self._count_lbl.setText(f"{len(snap.entities)} entities")
        self._minimap.set_data(snap.hero, snap.entities, snap.radius)
        self._model.set_entities(snap.entities)
