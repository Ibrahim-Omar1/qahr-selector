"""Read-only ESP radar dump — pure pymem, zero injection, no game-function calls.

Attaches to the live game and prints the hero plus nearby entities (the scene
roster) sorted by distance. Every read is defensive, so it's safe at any game
state. This is the manual verification runner for ``MemoryReader.entities()``.

Run with the game in-world:
    uv run python scripts/esp_dump.py [radius=32] [cycles=3]
"""
from __future__ import annotations

import sys
import time

from selector.engine.memory import MemoryReader
from selector.services.observability import logger, setup_logging


def _utf8_console() -> None:
    """Let the console print non-ASCII (e.g. Arabic) names without erroring."""
    for stream in (sys.stdout, sys.stderr):
        with_reconfig = getattr(stream, "reconfigure", None)
        if with_reconfig is not None:
            with_reconfig(encoding="utf-8", errors="replace")


def main() -> int:
    _utf8_console()
    setup_logging("logs")
    radius = int(sys.argv[1]) if len(sys.argv) > 1 else 32
    cycles = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    reader = MemoryReader()
    if not reader.attach():
        logger.error("could not attach — is Conquer.exe running and in-world?")
        return 1

    saw_entities = False
    try:
        for _ in range(cycles):
            hero = reader.hero()
            if hero is None:
                logger.warning("hero not in world yet — waiting")
                time.sleep(1.0)
                continue
            ents = reader.entities(radius=radius)
            saw_entities = saw_entities or bool(ents)
            logger.info(
                "hero {} (uid {}) @ ({},{}) — {} entities within {} tiles",
                hero.name, hero.uid, hero.x, hero.y, len(ents), radius,
            )
            for e in ents:
                logger.info(
                    "  {:<7} uid={:<9} {:<16} ({:>4},{:>4})  d={:<3} pk={}",
                    e.kind.value, e.uid, e.name or "-", e.x, e.y, e.dist, e.pk_name,
                )
            time.sleep(1.0)
    finally:
        reader.detach()

    if saw_entities:
        logger.success("PASS — radar decoded real neighbours read-only, clean detach")
        return 0
    logger.error("FAIL — no entities decoded (empty roster, or off-world)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
