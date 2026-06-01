"""Shared test setup: run Qt headless so UI tests need no display."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
