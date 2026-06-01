"""viewmodels/radar_vm — MVVM bridge between an engine and the radar view.

Polls the (swappable) ``EngineProtocol`` on a timer, packs a read-only snapshot,
and emits ``updated``. The view binds to that signal; it never touches the engine
directly. All engine calls are guarded so a transient read failure (zoning,
closed game) degrades to an empty snapshot rather than crashing the UI.
"""
from __future__ import annotations

import contextlib
from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QTimer, Signal

from selector.core.models import Entity, Hero
from selector.engine.protocol import EngineProtocol


@dataclass(frozen=True)
class RadarSnapshot:
    """An immutable frame of radar state for the view to render."""

    attached: bool = False
    hero: Hero | None = None
    entities: list[Entity] = field(default_factory=list)
    radius: int = 32


class RadarViewModel(QObject):
    """Drives the radar: polls the engine, exposes the latest snapshot."""

    updated = Signal()  # emitted after every poll

    def __init__(
        self,
        engine: EngineProtocol,
        interval_ms: int = 140,
        radius: int = 32,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._engine = engine
        self._radius = radius
        self._snap = RadarSnapshot(radius=radius)
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._tick)

    # ---- read surface for the view ------------------------------------------
    @property
    def snapshot(self) -> RadarSnapshot:
        return self._snap

    @property
    def engine_name(self) -> str:
        return self._engine.name

    # ---- control -------------------------------------------------------------
    def start(self) -> None:
        self._tick()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def set_radius(self, radius: int) -> None:
        self._radius = max(1, radius)

    def set_engine(self, engine: EngineProtocol) -> None:
        """Swap the backing engine (e.g. Mock <-> live), detaching the old one."""
        old, self._engine = self._engine, engine
        with contextlib.suppress(Exception):
            old.detach()
        self._tick()

    # ---- poll ----------------------------------------------------------------
    def _tick(self) -> None:
        eng = self._engine
        try:
            if not eng.attached():
                eng.attach()
            attached = eng.attached()
            hero = eng.hero() if attached else None
            ents = eng.entities(self._radius) if attached else []
        except Exception:
            attached, hero, ents = False, None, []
        self._snap = RadarSnapshot(
            attached=attached, hero=hero, entities=ents, radius=self._radius
        )
        self.updated.emit()
