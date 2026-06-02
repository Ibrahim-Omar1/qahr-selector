"""ui/main_window — the application shell.

Sidebar + a header (page title, hero/status, Mock⇄Live toggle) + a stacked
content area. Owns no engine logic: it reflects ``RadarViewModel`` state and
delegates the engine swap to an injected callback (composition root wires it).
"""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from selector.ui.pages.auto_page import AutoPage
from selector.ui.pages.radar_page import RadarPage
from selector.ui.sidebar import Sidebar
from selector.ui.theme import METRICS
from selector.viewmodels.auto_vm import AutoViewModel
from selector.viewmodels.radar_vm import RadarViewModel

_TITLES = ("Radar", "Auto", "Combat", "Movement", "Settings")


class MainWindow(QMainWindow):
    def __init__(
        self,
        vm: RadarViewModel,
        auto_vm: AutoViewModel,
        on_engine_change: Callable[[bool], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = vm
        self._auto_vm = auto_vm
        self._on_engine_change = on_engine_change
        self.setWindowTitle("Selector — Qahr Online")
        self.resize(1040, 660)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.navigate.connect(self._on_navigate)
        outer.addWidget(self._sidebar)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._build_header())

        self._stack = QStackedWidget()
        self._stack.addWidget(RadarPage(vm))                 # 0 Radar
        self._stack.addWidget(AutoPage(auto_vm))             # 1 Auto
        for title in _TITLES[2:]:                            # 2..4 placeholders
            self._stack.addWidget(self._placeholder(title))
        right.addWidget(self._stack, 1)
        outer.addLayout(right, 1)

        vm.updated.connect(self._update_status)
        self._update_status()

    # --- header ---------------------------------------------------------------
    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(METRICS.header_h)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(METRICS.pad_page, 0, METRICS.gutter, 0)
        lay.setSpacing(METRICS.gutter)

        self._title = QLabel(_TITLES[0])
        self._title.setObjectName("pageTitle")
        lay.addWidget(self._title)
        lay.addStretch(1)

        self._status = QLabel("—")
        self._status.setObjectName("status")
        lay.addWidget(self._status, 0, Qt.AlignmentFlag.AlignVCenter)

        self._toggle = QPushButton("Mock")
        self._toggle.setObjectName("toggle")
        self._toggle.setCheckable(True)
        self._toggle.setFixedHeight(METRICS.ctl_h)
        self._toggle.setFixedWidth(72)
        self._toggle.setToolTip("Switch between Mock data and the live game")
        self._toggle.toggled.connect(self._on_toggle)
        lay.addWidget(self._toggle, 0, Qt.AlignmentFlag.AlignVCenter)
        return header

    def _placeholder(self, title: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lab = QLabel(f"{title} — coming soon")
        lab.setObjectName("muted")
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lab)
        return w

    def set_live(self, live: bool) -> None:
        """Reflect an initial engine choice in the toggle (fires the swap)."""
        self._toggle.setChecked(live)

    # --- behaviour ------------------------------------------------------------
    def _on_navigate(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self._title.setText(_TITLES[index])

    def _on_toggle(self, live: bool) -> None:
        self._toggle.setText("Live" if live else "Mock")
        self._on_engine_change(live)
        self._update_status()

    def _update_status(self) -> None:
        snap = self._vm.snapshot
        live = self._toggle.isChecked()
        if not live:
            self._status.setText("● Mock data")
        elif snap.attached:
            self._status.setText("● Live · attached")
        else:
            self._status.setText("○ Live · waiting for game")
