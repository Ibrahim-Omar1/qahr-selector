"""engine/mock_engine — fake-but-believable engine for UI/dev with no game.

Implements the read surface of EngineProtocol so the UI runs standalone.
"""
from __future__ import annotations

import math

from selector.core.models import Entity, Hero, Relation
from selector.core.radar import chebyshev, classify


class MockEngine:
    """A demo engine producing a slowly-moving hero + a few nearby entities."""

    name = "mock"

    def __init__(self, hero_name: str = "DemoHero") -> None:
        self._hero_name = hero_name
        self._attached = False
        self._t = 0
        self._autopot: tuple[int | None, int | None] = (None, None)

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
        # HP/MP wander so the Auto page bars visibly move in the demo.
        hp = 5000 + int(3500 * math.sin(self._t / 20))
        mp = 3000 + int(2200 * math.cos(self._t / 16))
        return Hero(
            uid=1050859, name=self._hero_name, x=x, y=y, pk=0, speed=66,
            hp=hp, max_hp=8500, mp=mp, max_mp=5200,
        )

    def selected_uid(self) -> int | None:
        return 1007799

    def set_autopot(self, hp_pct: int | None, mp_pct: int | None) -> bool:
        self._autopot = (hp_pct, mp_pct)  # demo: just remember it
        return self._attached

    def entities(self, radius: int = 64) -> list[Entity]:
        if not self._attached:
            return []
        h = self.hero()
        hx, hy = (h.x, h.y) if h else (300, 300)
        hero_uid = h.uid if h else None
        sel = self.selected_uid()
        # uids chosen to land in distinct bands: player (>999999), monster
        # (500001..999999), NPC (<500001); "Sadistic" == selected -> TARGET.
        # uid, name, x, y, pk, guild, gid, relation
        seed = [
            (1050860, "Reaper", hx + 4, hy + 2, 0, "Vanguard", 26, Relation.GUILDMATE),
            (1050861, "Aegis", hx - 5, hy + 3, 0, "Bastion", 76, Relation.ALLY),
            (1050862, "Ruin", hx + 6, hy - 4, 0, "Crimson", 3, Relation.ENEMY),
            (700123, "Turtle", hx - 6, hy + 1, 0, "", 0, Relation.NEUTRAL),
            (12345, "Merchant", hx + 9, hy - 2, 1, "", 0, Relation.NEUTRAL),
            (1007799, "Sadistic", hx + 1, hy - 3, 3, "Vanguard", 26, Relation.GUILDMATE),
        ]
        return [
            Entity(
                uid=uid, name=name, x=x, y=y, pk=pk,
                kind=classify(uid, selected_uid=sel, hero_uid=hero_uid),
                dist=chebyshev(hx, hy, x, y),
                guild=guild, guild_id=gid, relation=rel,
            )
            for uid, name, x, y, pk, guild, gid, rel in seed
        ]
