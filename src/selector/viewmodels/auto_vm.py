"""viewmodels/auto_vm — thin controller for Auto-HP.

Auto-HP is just "write two values" (enable + HP% threshold) and the game drinks
on its own thread — there's nothing to poll, so this is a small plain controller,
not a QTimer view-model. Holds the active engine and re-applies on change/swap.
"""
from __future__ import annotations

from selector.engine.protocol import EngineProtocol

_DEFAULT_PCT = 60


class AutoController:
    """Applies the Auto-HP setting (enable + threshold) to the current engine."""

    def __init__(self, engine: EngineProtocol) -> None:
        self._engine = engine
        self._enabled = False
        self._pct = _DEFAULT_PCT

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def pct(self) -> int:
        return self._pct

    def set_engine(self, engine: EngineProtocol) -> None:
        self._engine = engine
        self._apply()

    def set_enabled(self, on: bool) -> bool:
        self._enabled = on
        return self._apply()

    def set_pct(self, pct: int) -> bool:
        self._pct = max(5, min(95, pct))
        return self._apply()

    def _apply(self) -> bool:
        try:
            if not self._engine.attached():
                self._engine.attach()
            return self._engine.set_auto_hp(self._pct if self._enabled else None)
        except Exception:
            return False
