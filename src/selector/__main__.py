"""Entry point — intentionally thin.

Parses args, builds the app via the composition root, runs it.
    uv run selector            # Mock data (no game needed)
    uv run selector --live     # attach to the live game
"""
from __future__ import annotations

import sys


def main() -> int:
    from selector.app.bootstrap import build

    app, window = build(live="--live" in sys.argv)
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    sys.exit(main())
