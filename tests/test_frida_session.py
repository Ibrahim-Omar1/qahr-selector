"""No-game tests for the Frida session wrapper + agent (task #27)."""
from __future__ import annotations

import json

from selector.core.offsets import CURRENT
from selector.engine import frida_session
from selector.engine.frida_session import FridaSession


def test_config_injection_is_valid_json() -> None:
    cfg = CURRENT.to_agent_config()
    again = json.loads(json.dumps(cfg))  # the exact blob we prepend as CONFIG
    assert again["module"] == "Conquer.exe"
    assert "structs" in again and "globals" in again
    assert again["structs"]["coordShift"] == 6


def test_agent_file_present_and_shaped() -> None:
    src = frida_session._AGENT_PATH.read_text(encoding="utf-8")
    assert "PeekMessage" in src       # system per-frame tick (not game .text)
    assert "rpc.exports" in src
    assert "Interceptor.attach" in src
    assert "new NativeFunction(" not in src  # read-only proof: no game-function calls


def test_attach_unknown_process_fails_cleanly() -> None:
    s = FridaSession()
    assert s.attach("___no_such_process___.exe") is False
    assert s.attached() is False
    assert s.ping() is None
    assert s.frame_count() is None
