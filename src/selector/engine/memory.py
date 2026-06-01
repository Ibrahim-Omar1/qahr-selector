"""engine/memory — read-only game state via pymem.

No hooks, no writes — just resolves the hero/entity state from `core.offsets`.
Every read is defensive: a bad/failed read yields ``None`` and never raises, so
the UI's refresh loop is safe at any game state (loading, zoning, closed).

Selected target + full entity enumeration are NOT done here (they need the
per-frame agent / a container walk — later milestones). This layer proves the
read path: attach + hero.
"""
from __future__ import annotations

import contextlib
from typing import Any

from selector.core.models import Entity, Hero
from selector.core.offsets import CURRENT, GameTarget

try:
    import pymem
except Exception:  # pragma: no cover - pymem optional at import time
    pymem = None


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
        # Reliable only via the SELECT hook (agent milestone); read-only can't.
        return None

    def entities(self) -> list[Entity]:
        # Full enumeration needs the agent / a container walk (later milestone).
        return []
