"""engine/frida_session — load the Frida agent + RPC, with observability wired.

Injects the active version's offsets (``core.offsets``) into the agent as
``CONFIG``, routes Frida detach/error events into the log (``wire_frida``), and
exposes the agent's RPC. Read-only at this stage — the agent calls no game
functions, only hooks a system per-frame function and reads.
"""
from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any

from selector.core.offsets import CURRENT, GameTarget
from selector.services.observability import logger, wire_frida

try:
    import frida
except Exception:  # pragma: no cover - frida optional at import time
    frida = None  # type: ignore[assignment]

_AGENT_PATH = Path(__file__).resolve().parent / "agent" / "conquer.js"


class FridaSession:
    """Attach to the game, inject CONFIG+agent, expose RPC. Fully defensive."""

    def __init__(self, target: GameTarget = CURRENT) -> None:
        self.target = target
        self._session: Any = None
        self._script: Any = None
        self._rpc: Any = None

    # ---- lifecycle -----------------------------------------------------------
    def attach(self, who: int | str | None = None) -> bool:
        if frida is None:
            logger.error("frida is not installed (pip install frida)")
            return False
        target: int | str = who if who is not None else self.target.module
        try:
            self._session = frida.attach(target)
        except Exception as e:  # noqa: BLE001 - reported, never propagated
            logger.error("frida attach failed for {!r}: {}", target, e)
            return False
        try:
            self._load_agent()
        except Exception:
            logger.exception("agent load failed")
            self.detach()
            return False
        wire_frida(self._session, self._script, label="Conquer")
        logger.success("Frida agent loaded (target={!r})", target)
        return True

    def _load_agent(self) -> None:
        src = _AGENT_PATH.read_text(encoding="utf-8")
        config_js = f"const CONFIG = {json.dumps(self.target.to_agent_config())};\n"
        self._script = self._session.create_script(config_js + src)
        self._script.load()
        self._rpc = getattr(self._script, "exports_sync", None) or self._script.exports

    def attached(self) -> bool:
        return self._session is not None and self._rpc is not None

    def detach(self) -> None:
        if self._script is not None:
            with contextlib.suppress(Exception):
                self._script.unload()
        if self._session is not None:
            with contextlib.suppress(Exception):
                self._session.detach()
        self._session = self._script = self._rpc = None

    # ---- RPC passthrough (returns are dynamic JSON from the agent) -----------
    def ping(self) -> Any:
        return self._rpc.ping() if self._rpc else None

    def frames(self) -> Any:
        return self._rpc.frames() if self._rpc else None

    def hero(self) -> Any:
        return self._rpc.hero() if self._rpc else None

    def frame_count(self) -> int | None:
        f = self.frames()
        if isinstance(f, dict):
            c = f.get("count")
            return int(c) if isinstance(c, int) else None
        return None
