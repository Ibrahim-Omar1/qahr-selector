"""viewmodels/auto_vm — MVVM bridge for the Auto-HP / Auto-Mana feature.

Polls the engine for the hero's HP/MP (to drive the live bars) and applies the
user's threshold settings to the game via ``engine.set_autopot`` (mechanism A:
a settings write that drives the game's own auto-pot). The view only calls the
setters; it never touches the engine directly.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QTimer, Signal

from selector.core.models import Hero
from selector.engine.protocol import EngineProtocol

_HP_DEFAULT = 60
_MP_DEFAULT = 40


@dataclass(frozen=True)
class AutoSnapshot:
    """An immutable frame of auto-feature state for the view."""

    attached: bool = False
    hero: Hero | None = None
    hp_enabled: bool = False
    hp_pct: int = _HP_DEFAULT
    mp_enabled: bool = False
    mp_pct: int = _MP_DEFAULT
    applied: bool = False  # did the last settings write reach the game?


class AutoViewModel(QObject):
    """Drives Auto-HP/Mana: live HP/MP read-out + applies threshold settings."""

    updated = Signal()

    def __init__(
        self,
        engine: EngineProtocol,
        interval_ms: int = 200,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._engine = engine
        self._hp_on = False
        self._hp_pct = _HP_DEFAULT
        self._mp_on = False
        self._mp_pct = _MP_DEFAULT
        self._applied = False
        self._snap = AutoSnapshot()
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._tick)

    @property
    def snapshot(self) -> AutoSnapshot:
        return self._snap

    # ---- control -------------------------------------------------------------
    def start(self) -> None:
        self._tick()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def set_hp_enabled(self, on: bool) -> None:
        self._hp_on = on
        self._apply()

    def set_hp_pct(self, pct: int) -> None:
        self._hp_pct = _clamp(pct)
        self._apply()  # a disabled pot is passed as None, so no game write for it

    def set_mp_enabled(self, on: bool) -> None:
        self._mp_on = on
        self._apply()

    def set_mp_pct(self, pct: int) -> None:
        self._mp_pct = _clamp(pct)
        self._apply()

    def set_engine(self, engine: EngineProtocol) -> None:
        self._engine = engine
        self._apply()

    # ---- internals -----------------------------------------------------------
    def _apply(self) -> None:
        """Push the current thresholds to the game (None = that pot disabled)."""
        try:
            self._applied = self._engine.set_autopot(
                self._hp_pct if self._hp_on else None,
                self._mp_pct if self._mp_on else None,
            )
        except Exception:
            self._applied = False
        self._tick()

    def _tick(self) -> None:
        eng = self._engine
        try:
            if not eng.attached():
                eng.attach()
            attached = eng.attached()
            hero = eng.hero() if attached else None
        except Exception:
            attached, hero = False, None
        self._snap = AutoSnapshot(
            attached=attached, hero=hero,
            hp_enabled=self._hp_on, hp_pct=self._hp_pct,
            mp_enabled=self._mp_on, mp_pct=self._mp_pct,
            applied=self._applied,
        )
        self.updated.emit()


def _clamp(pct: int) -> int:
    return max(5, min(95, pct))
