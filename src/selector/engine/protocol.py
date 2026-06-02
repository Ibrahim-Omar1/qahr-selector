"""engine/protocol — the contract every engine (real / mock) satisfies.

Structural (PEP 544) so the UI/services depend on the interface, not a concrete
engine. Starts read-only; feature-control methods are added as features land.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from selector.core.models import Entity, Hero


@runtime_checkable
class EngineProtocol(Protocol):
    """Read-only surface of a game engine (this milestone)."""

    name: str

    def attach(self) -> bool: ...
    def attached(self) -> bool: ...
    def hero(self) -> Hero | None: ...
    def selected_uid(self) -> int | None: ...
    def entities(self, radius: int = 64) -> list[Entity]: ...
    def detach(self) -> None: ...

    # Drive the game's native auto-HP-pot: `pct` is the trigger threshold (drink
    # below pct% HP), or None to disable. Returns True if applied. (A memory write.)
    def set_auto_hp(self, pct: int | None) -> bool: ...
