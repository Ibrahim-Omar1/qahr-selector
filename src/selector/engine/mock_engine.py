"""engine/mock_engine — fake-but-believable engine for UI/dev with no game.

Implements the read surface of EngineProtocol so the UI runs standalone.
"""
from __future__ import annotations

import math

from selector.core.models import Entity, Hero
from selector.core.radar import chebyshev, classify


class MockEngine:
    """A demo engine producing a slowly-moving hero + a few nearby entities."""

    name = "mock"

    def __init__(self, hero_name: str = "DemoHero") -> None:
        self._hero_name = hero_name
        self._attached = False
        self._t = 0

    def attach(self) -> bool:
        self._attached = True
        return True

    def attached(self) -> bool:
        return self._attached

    def detach(self) -> None:
        self._attached = False

    def hero(self) -> Hero | None:
        if not self._attached:
            return None
        self._t += 1
        x = 300 + int(8 * math.cos(self._t / 12))
        y = 300 + int(8 * math.sin(self._t / 12))
        return Hero(uid=1050859, name=self._hero_name, x=x, y=y, pk=0, speed=66)

    def selected_uid(self) -> int | None:
        return 1007799

    def entities(self, radius: int = 64) -> list[Entity]:
        if not self._attached:
            return []
        h = self.hero()
        hx, hy = (h.x, h.y) if h else (300, 300)
        hero_uid = h.uid if h else None
        sel = self.selected_uid()
        # uids chosen to land in distinct bands: player (>999999), monster
        # (500001..999999), NPC (<500001); "Sadistic" == selected -> TARGET.
        seed = [
            (1050860, "Reaper", hx + 4, hy + 2, 0, "Vanguard"),
            (700123, "Turtle", hx - 6, hy + 1, 0, ""),
            (12345, "Merchant", hx + 9, hy - 2, 1, ""),
            (1007799, "Sadistic", hx + 1, hy - 3, 3, "Vanguard"),
        ]
        return [
            Entity(
                uid=uid, name=name, x=x, y=y, pk=pk,
                kind=classify(uid, selected_uid=sel, hero_uid=hero_uid),
                dist=chebyshev(hx, hy, x, y),
                guild=guild,
            )
            for uid, name, x, y, pk, guild in seed
        ]
