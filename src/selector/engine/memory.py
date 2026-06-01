"""engine/memory — read-only game state via pymem.

No hooks, no writes — just resolves the hero/entity state from `core.offsets`.
Every read is defensive: a bad/failed read yields ``None`` and never raises, so
the UI's refresh loop is safe at any game state (loading, zoning, closed).

The hero is read directly (zero injection). The selected-target UID and full
entity enumeration (the radar) are the remaining pieces — see ``selected_uid``
and ``entities`` for what's still needed.
"""
from __future__ import annotations

import contextlib
import struct
from typing import Any

from selector.core.models import Entity, Hero
from selector.core.offsets import CURRENT, GameTarget
from selector.core.radar import chebyshev, classify, relation

try:
    import pymem
except Exception:  # pragma: no cover - pymem optional at import time
    pymem = None

# Hard cap on the roster walk so a torn/garbage count can never spin the loop.
MAX_ENTITIES = 4096


class MemoryReader:
    """pymem-backed read-only engine (implements the read half of EngineProtocol)."""

    name = "pymem"

    def __init__(self, target: GameTarget = CURRENT) -> None:
        self.target = target
        self._pm: Any = None        # pymem.Pymem (untyped lib) or None
        self._base: int = 0

    # ---- lifecycle -----------------------------------------------------------
    def attach(self) -> bool:
        if pymem is None:
            return False
        try:
            pm = pymem.Pymem(self.target.module)
            self._pm = pm
            self._base = int(pm.base_address)
            return True
        except Exception:
            self._pm = None
            return False

    def attached(self) -> bool:
        return self._pm is not None

    def detach(self) -> None:
        pm, self._pm, self._base = self._pm, None, 0
        if pm is not None:
            with contextlib.suppress(Exception):
                pm.close_process()

    # ---- low-level reads (all defensive) ------------------------------------
    def _rebase(self, va: int) -> int:
        """Static VA -> live address for this module load."""
        return self._base + (va - self.target.image_base)

    def _u32(self, addr: int) -> int | None:
        if not addr or self._pm is None:
            return None
        try:
            return int(self._pm.read_uint(addr))
        except Exception:
            return None

    def _u32_va(self, va: int) -> int | None:
        return self._u32(self._rebase(va))

    def _utf16(self, addr: int, max_bytes: int = 64) -> str:
        if not addr or self._pm is None:
            return ""
        try:
            raw = self._pm.read_bytes(addr, max_bytes)
        except Exception:
            return ""
        text: str = bytes(raw).decode("utf-16-le", errors="ignore")
        return text.split("\x00", 1)[0]

    # ---- decoded state -------------------------------------------------------
    def _coords(self, obj: int) -> tuple[int, int] | None:
        st = self.target.structs
        sub = self._u32(obj + st.coord_sub)
        if not sub:
            return None
        x = self._u32(sub + st.coord_x)
        y = self._u32(sub + st.coord_y)
        if x is None or y is None:
            return None
        return (x >> st.coord_shift, y >> st.coord_shift)

    def _hero_ptr(self) -> int | None:
        return self._u32_va(self.target.globals["heroSlot"])

    def hero(self) -> Hero | None:
        st = self.target.structs
        p = self._hero_ptr()
        if not p:
            return None
        uid = self._u32(p + st.uid)
        if uid is None:
            return None
        xy = self._coords(p)
        if xy is None:
            return None
        name_ptr = self._u32(p + st.name)
        return Hero(
            uid=uid,
            name=self._utf16(name_ptr) if name_ptr else "",
            x=xy[0],
            y=xy[1],
            pk=self._u32(p + st.pk),
            speed=self._u32(p + st.speed),
        )

    def selected_uid(self) -> int | None:
        """Currently selected target UID — NOT yet available read-only.

        Ruled out live: ``[camSlot]+0x11208`` returns a constant (~6029428) that
        does NOT track selection, and the ``[0x1A0D628]`` global reads 0. The
        scene object the game's SELECT handler writes (``0x4D79FB``) isn't held
        by any known global; the reliable source is the SELECT hook (agent) or a
        differential-scan-confirmed global. Until then this is honestly None.
        """
        return None

    def _roster_entity_ptr(self, _map: int, mapsize: int, myoff: int, i: int) -> int | None:
        """Resolve the i-th roster element to its entity-object pointer.

        The roster's storage is an MSVC ``std::deque`` of 8-byte elements
        (entity ptr at +0). See ``RosterLayout`` for the formula.
        """
        r = self.target.roster
        g = myoff + i
        block = self._u32(_map + ((g // r.block_elems) % mapsize) * 4)
        if not block:
            return None
        return self._u32(block + (g % r.block_elems) * r.elem_size) or None

    def _read_uid_vector(self, begin_name: str, end_name: str) -> frozenset[int]:
        """Read a std::vector<uint32> of UIDs (begin/end global slots) into a set."""
        begin = self._u32_va(self.target.globals[begin_name])
        end = self._u32_va(self.target.globals[end_name])
        if not begin or not end or end <= begin or (end - begin) % 4:
            return frozenset()
        n = (end - begin) // 4
        if n > MAX_ENTITIES or self._pm is None:
            return frozenset()
        try:
            raw = self._pm.read_bytes(begin, end - begin)
        except Exception:
            return frozenset()
        return frozenset(struct.unpack(f"<{n}I", raw))

    def _decode_entity(
        self,
        ep: int,
        hero: Hero,
        selected: int | None,
        monsters: frozenset[int],
        hero_syndicate_id: int,
    ) -> Entity | None:
        """Decode one entity-object pointer into an ``Entity`` (None if unusable)."""
        st = self.target.structs
        uid = self._u32(ep + st.uid)
        if not uid:
            return None
        xy = self._coords(ep)
        if xy is None:
            return None
        # syndicate id gates the (otherwise stale) guild-name pointer.
        synid = self._u32(ep + st.syndicate_id) or 0
        guild = ""
        if synid:
            gp = self._u32(ep + st.syndicate_name)
            guild = self._utf16(gp) if gp else ""
        name_ptr = self._u32(ep + st.name)
        return Entity(
            uid=uid,
            name=self._utf16(name_ptr) if name_ptr else "",
            x=xy[0],
            y=xy[1],
            pk=self._u32(ep + st.pk),
            kind=classify(uid, selected_uid=selected, hero_uid=hero.uid, monsters=monsters),
            dist=chebyshev(hero.x, hero.y, xy[0], xy[1]),
            guild=guild,
            relation=relation(
                uid, synid, hero_uid=hero.uid, hero_syndicate_id=hero_syndicate_id
            ),
        )

    def entities(self, radius: int = 64) -> list[Entity]:
        """Read-only radar: nearby entities within ``radius`` tiles, sorted by distance.

        Walks the scene roster (``RosterLayout``) — pure pymem, zero injection.
        Returns [] off-world or if the roster can't be resolved.
        """
        hero = self.hero()
        if hero is None:
            return []
        r = self.target.roster
        cb = self._rebase(r.container)
        count = self._u32(cb + r.count)
        _map = self._u32(cb + r.map_ptr)
        mapsize = self._u32(cb + r.map_size)
        myoff = self._u32(cb + r.front_off)
        if not count or not _map or not mapsize or myoff is None:
            return []
        selected = self.selected_uid()
        monsters = self._read_uid_vector("monsterVecBegin", "monsterVecEnd")
        hero_ptr = self._hero_ptr()
        hero_syn = (self._u32(hero_ptr + self.target.structs.syndicate_id) or 0) if hero_ptr else 0
        out: list[Entity] = []
        for i in range(min(count, MAX_ENTITIES)):
            ep = self._roster_entity_ptr(_map, mapsize, myoff, i)
            if ep is None:
                continue
            ent = self._decode_entity(ep, hero, selected, monsters, hero_syn)
            if ent is not None and ent.dist <= radius:
                out.append(ent)
        out.sort(key=lambda e: e.dist)
        return out
