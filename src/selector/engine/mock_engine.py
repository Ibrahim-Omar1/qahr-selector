"""engine/mock_engine — fake-but-believable engine for UI/dev with no game.

Implements the read surface of EngineProtocol so the UI runs standalone.
"""
from __future__ import annotations

import math

from selector.core.models import Entity, Hero


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

    def entities(self) -> list[Entity]:
        if not self._attached:
            return []
        h = self.hero()
        hx, hy = (h.x, h.y) if h else (300, 300)
        seed = [
            (23058, "Reaper", hx + 4, hy + 2, 0, "player"),
            (1000360, "Turtle", hx - 6, hy + 1, 0, "monster"),
            (1007799, "Sadistic", hx + 1, hy - 3, 3, "target"),
        ]
        out: list[Entity] = []
        for uid, name, x, y, pk, kind in seed:
            out.append(
                Entity(uid=uid, name=name, x=x, y=y, pk=pk, kind=kind,
                       dist=max(abs(x - hx), abs(y - hy)))
            )
        return out
