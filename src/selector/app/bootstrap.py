"""app/bootstrap — composition root.

The one place engines, view-models, and views are wired together. Nothing here
holds global state; ``build`` returns the app + window for the entry point to run.
"""
from __future__ import annotations

from PySide6.QtWidgets import QApplication

from selector.engine.memory import MemoryReader
from selector.engine.mock_engine import MockEngine
from selector.engine.protocol import EngineProtocol
from selector.ui.main_window import MainWindow
from selector.ui.theme import qss
from selector.viewmodels.auto_vm import AutoViewModel
from selector.viewmodels.radar_vm import RadarViewModel


def make_engine(live: bool) -> EngineProtocol:
    """Live game (pymem) when ``live``, else the no-game Mock."""
    return MemoryReader() if live else MockEngine()


def build(live: bool = False) -> tuple[QApplication, MainWindow]:
    """Wire engine → view-models → window and return (app, window)."""
    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication([])
    app.setStyleSheet(qss())

    engine = MockEngine()
    radar_vm = RadarViewModel(engine)
    auto_vm = AutoViewModel(engine)

    def on_engine_change(is_live: bool) -> None:
        eng = make_engine(is_live)  # one engine instance shared by both view-models
        radar_vm.set_engine(eng)
        auto_vm.set_engine(eng)

    window = MainWindow(radar_vm, auto_vm, on_engine_change)
    if live:
        window.set_live(True)
    radar_vm.start()
    auto_vm.start()
    return app, window
