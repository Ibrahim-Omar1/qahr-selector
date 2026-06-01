"""services/observability — app-wide logging + crash/freeze detection.

One place that configures everything:
  * **loguru** — rotating/compressed file logs + a console sink, with rich
    tracebacks; thread-safe (``enqueue``) so Frida/Qt callbacks can log freely.
  * **faulthandler** — dumps a native traceback (all threads) to a file on a
    hard crash (SIGSEGV/SIGABRT) — pymem/frida make native calls that can do
    this, and a normal logger can't capture it.
  * **excepthooks** — uncaught Python exceptions (main + threads) -> loguru.
  * **wire_frida** — routes a Frida session/script's events into the log so a
    game crash ("detached", with reason) or agent JS error always lands next to
    the last thing we did.
  * **Watchdog** — warns if a frame/tick counter stalls (freeze detection).

Import ``logger`` from here everywhere; call ``setup_logging`` once at startup.
"""
from __future__ import annotations

import faulthandler
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import IO, Any

from loguru import logger

__all__ = ["logger", "setup_logging", "wire_frida", "Watchdog"]

_CONSOLE_FMT = (
    "<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | "
    "<cyan>{name}</cyan> - {message}"
)
_FILE_FMT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <7} | {name}:{function}:{line} | "
    "{message}"
)

_fault_fp: IO[str] | None = None  # keep the faulthandler file alive


def setup_logging(
    log_dir: Path | str = "logs",
    *,
    level: str = "DEBUG",
    console: bool = True,
) -> Path:
    """Configure loguru sinks + faulthandler + excepthooks. Returns the log dir."""
    global _fault_fp
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()  # drop loguru's default stderr handler
    if console:
        logger.add(sys.stderr, level=level, format=_CONSOLE_FMT,
                   backtrace=True, diagnose=False, colorize=True)
    logger.add(
        str(log_dir / "selector_{time:YYYYMMDD_HHmmss}.log"),
        level="DEBUG",
        format=_FILE_FMT,
        rotation="5 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,       # thread-safe (Frida/Qt callbacks)
        backtrace=True,
        diagnose=True,
    )

    # native crash dumps (segfault/abort from pymem/frida) -> their own file
    if _fault_fp is None:
        _fault_fp = (log_dir / "faulthandler.log").open("a", buffering=1, encoding="utf-8")
        faulthandler.enable(file=_fault_fp, all_threads=True)

    _install_excepthooks()
    logger.info("logging initialised (dir={})", log_dir)
    return log_dir


def _install_excepthooks() -> None:
    def _main_hook(
        exc_type: type[BaseException],
        exc: BaseException,
        tb: TracebackType | None,
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        logger.opt(exception=(exc_type, exc, tb)).critical("UNCAUGHT exception")

    def _thread_hook(args: threading.ExceptHookArgs) -> None:
        name = args.thread.name if args.thread else "?"
        logger.opt(exception=(args.exc_type, args.exc_value, args.exc_traceback)).error(
            "uncaught exception in thread {}", name
        )

    sys.excepthook = _main_hook
    threading.excepthook = _thread_hook


def wire_frida(session: Any, script: Any | None = None, *, label: str = "game") -> None:
    """Route a Frida session/script's events into the log.

    ``session.on('detached')`` => game crash/close (with reason);
    ``script.on('message')``  => agent ``send()`` payloads + JS errors.
    Defensive — never raises if the Frida API shape differs.
    """

    def on_detached(reason: Any = None, *_rest: Any) -> None:
        logger.warning("{} DETACHED — reason={!r}", label, reason)

    try:
        session.on("detached", on_detached)
    except Exception as e:  # noqa: BLE001 - diagnostic only
        logger.debug("could not wire session.detached: {}", e)

    if script is not None:
        def on_message(message: Any, _data: Any = None) -> None:
            mtype = message.get("type") if isinstance(message, dict) else None
            if mtype == "error":
                logger.error("agent JS error: {} | {}", message.get("description"),
                             message.get("stack"))
            elif mtype == "send":
                logger.debug("agent: {}", message.get("payload"))

        try:
            script.on("message", on_message)
        except Exception as e:  # noqa: BLE001
            logger.debug("could not wire script.message: {}", e)


class Watchdog:
    """Warn (once) if a monotonic counter stalls — freeze detection.

    Polls ``get_count`` every ``interval`` s; if it doesn't advance for
    ``stall_after`` consecutive polls *while* ``is_active()`` is True, logs a
    warning. Resets when the counter advances or activity stops. Daemon thread.
    """

    def __init__(
        self,
        get_count: Callable[[], int | None],
        *,
        is_active: Callable[[], bool] = lambda: True,
        interval: float = 2.0,
        stall_after: int = 3,
        name: str = "tick",
    ) -> None:
        self._get = get_count
        self._active = is_active
        self._interval = interval
        self._stall_after = stall_after
        self._name = name
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run, name=f"watchdog-{self._name}", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        last: int | None = None
        stalled = 0
        warned = False
        while not self._stop.wait(self._interval):
            if not self._active():
                last, stalled, warned = None, 0, False
                continue
            try:
                cur = self._get()
            except Exception:  # noqa: BLE001 - diagnostic poll
                cur = None
            if cur is None:
                continue
            if last is not None and cur == last:
                stalled += 1
                if stalled >= self._stall_after and not warned:
                    logger.warning(
                        "{} STALLED at {} for {} polls — possible freeze",
                        self._name, cur, stalled,
                    )
                    warned = True
            else:
                stalled, warned = 0, False
            last = cur
