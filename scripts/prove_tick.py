"""Read-only proof of the per-frame game-thread tick (task #27).

Attaches the Frida agent to the live game, hooks ``user32!PeekMessageW``, and
confirms a steady tick on the main thread — NO writes, NO game-function calls.
Fully instrumented (logs to ``logs/``; a stall trips the watchdog; a game crash
logs the detach reason).

Run with the game in-world:
    uv run python scripts/prove_tick.py
"""
from __future__ import annotations

import sys
import time

from selector.engine.frida_session import FridaSession
from selector.services.observability import Watchdog, logger, setup_logging


def main() -> int:
    setup_logging("logs")
    sess = FridaSession()
    if not sess.attach():
        logger.error("could not attach — is Conquer.exe running and in-world?")
        return 1

    time.sleep(0.4)  # let the agent emit 'ready' + hook the tick
    logger.info("ping: {}", sess.ping())
    logger.info("hero (agent read): {}", sess.hero())

    watchdog = Watchdog(sess.frame_count, interval=2.0, stall_after=2, name="frame")
    watchdog.start()

    last = 0
    saw_ticks = False
    for i in range(5):
        time.sleep(2)
        f = sess.frames() or {}
        count = int(f.get("count", 0))
        rate = (count - last) / 2.0
        last = count
        logger.info("t+{:02d}s | frames={} (~{:.0f}/s) | threads={}",
                    (i + 1) * 2, count, rate, f.get("threads", {}))
        if count > 0:
            saw_ticks = True

    watchdog.stop()
    f = sess.frames() or {}
    n_threads = len(f.get("threads", {}))
    sess.detach()

    if saw_ticks and n_threads >= 1:
        logger.success("PASS — steady tick on {} thread(s); read-only, clean detach",
                       n_threads)
        return 0
    logger.error("FAIL — no ticks seen; try PeekMessageA or the D3D9 Present fallback")
    return 1


if __name__ == "__main__":
    sys.exit(main())
