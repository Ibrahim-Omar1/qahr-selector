"""No-game tests for Hero HP/MP math + the Auto view-model (headless via conftest)."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from PySide6.QtWidgets import QApplication

from selector.core.models import Hero
from selector.engine.mock_engine import MockEngine
from selector.viewmodels.auto_vm import AutoViewModel


@pytest.fixture(scope="module")
def app() -> Iterator[QApplication]:
    instance = QApplication.instance()
    yield instance if isinstance(instance, QApplication) else QApplication([])


def test_hero_pct_math() -> None:
    h = Hero(uid=1, name="x", x=0, y=0, pk=0, speed=0, hp=50, max_hp=100, mp=30, max_mp=120)
    assert h.hp_pct == 50
    assert h.mp_pct == 25
    # missing/zero data -> None, never a crash
    assert Hero(uid=1, name="x", x=0, y=0, pk=0, speed=0).hp_pct is None
    assert Hero(uid=1, name="x", x=0, y=0, pk=0, speed=0, hp=5, max_hp=0).hp_pct is None


def test_mock_hero_has_vitals() -> None:
    e = MockEngine()
    e.attach()
    h = e.hero()
    assert h is not None
    assert h.hp_pct is not None and 0 <= h.hp_pct <= 100
    assert h.mp_pct is not None and 0 <= h.mp_pct <= 100


def test_auto_vm_apply_and_clamp(app: QApplication) -> None:
    vm = AutoViewModel(MockEngine())
    vm.start()
    assert vm.snapshot.hero is not None

    vm.set_hp_enabled(True)
    vm.set_hp_pct(70)
    assert vm.snapshot.hp_enabled is True
    assert vm.snapshot.hp_pct == 70
    assert vm.snapshot.applied is True  # MockEngine.set_autopot returns True when attached

    vm.set_mp_pct(200)  # clamp to 95
    assert vm.snapshot.mp_pct == 95
    vm.set_hp_pct(1)  # clamp to 5
    assert vm.snapshot.hp_pct == 5

    vm.set_hp_enabled(False)
    assert vm.snapshot.hp_enabled is False
    vm.stop()
