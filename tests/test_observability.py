"""Tests for the observability layer (logging + Frida wiring + watchdog)."""
from __future__ import annotations

from pathlib import Path

from loguru import logger

from selector.services.observability import Watchdog, setup_logging, wire_frida


def test_setup_logging_creates_log_file(tmp_path: Path) -> None:
    try:
        setup_logging(tmp_path, console=False)
        logger.info("hello from test")
        assert list(tmp_path.glob("selector_*.log")), "no log file created"
        assert (tmp_path / "faulthandler.log").exists()
    finally:
        logger.remove()  # don't leak sinks pointing at the tmp dir


class _FakeFridaEndpoint:
    def __init__(self) -> None:
        self.handlers: dict[str, object] = {}

    def on(self, event: str, cb: object) -> None:
        self.handlers[event] = cb


def test_wire_frida_registers_and_invokes() -> None:
    session = _FakeFridaEndpoint()
    script = _FakeFridaEndpoint()
    wire_frida(session, script, label="test")

    assert "detached" in session.handlers
    assert "message" in script.handlers

    # invoking the handlers must not raise
    session.handlers["detached"]("process-terminated")  # type: ignore[operator]
    script.handlers["message"](  # type: ignore[operator]
        {"type": "error", "description": "boom", "stack": "x"}, None
    )
    script.handlers["message"]({"type": "send", "payload": {"k": 1}}, None)  # type: ignore[operator]


def test_watchdog_start_stop_is_clean() -> None:
    wd = Watchdog(lambda: 0, interval=0.01, stall_after=2, name="t")
    wd.start()
    wd.start()  # idempotent — second start is a no-op
    wd.stop()
