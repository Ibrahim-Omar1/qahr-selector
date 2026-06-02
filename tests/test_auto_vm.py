"""No-game tests for the Auto-HP controller."""
from __future__ import annotations

from selector.engine.mock_engine import MockEngine
from selector.viewmodels.auto_vm import AutoController


def test_auto_controller_apply_and_clamp() -> None:
    c = AutoController(MockEngine())  # attaches lazily on first apply

    assert c.set_enabled(True) is True   # MockEngine.set_auto_hp returns True once attached
    assert c.enabled is True

    assert c.set_pct(70) is True
    assert c.pct == 70

    c.set_pct(200)   # clamp high
    assert c.pct == 95
    c.set_pct(1)     # clamp low
    assert c.pct == 5

    assert c.set_enabled(False) is True
    assert c.enabled is False
