"""No-game UI smoke tests (headless via conftest's offscreen platform)."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from PySide6.QtWidgets import QApplication

from selector.app.bootstrap import build
from selector.engine.mock_engine import MockEngine
from selector.ui.main_window import MainWindow
from selector.viewmodels.radar_vm import RadarViewModel


@pytest.fixture(scope="module")
def app() -> Iterator[QApplication]:
    instance = QApplication.instance()
    yield instance if isinstance(instance, QApplication) else QApplication([])


def test_app_builds_with_mock(app: QApplication) -> None:
    _, window = build(live=False)
    assert isinstance(window, MainWindow)


def test_radar_vm_polls_mock(app: QApplication) -> None:
    vm = RadarViewModel(MockEngine())
    vm.start()  # _tick() runs synchronously, so the snapshot is populated now
    snap = vm.snapshot
    assert snap.attached is True
    assert len(snap.entities) >= 1
    vm.stop()
