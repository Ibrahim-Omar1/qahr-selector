"""Entry point — intentionally thin.

Parses CLI args, builds the application via the composition root
(`selector.app.bootstrap`), and runs it. No logic lives here.
"""
from __future__ import annotations


def main() -> int:
    # Wired up in app/bootstrap.py once the foundation lands.
    raise SystemExit("selector: scaffold only — not implemented yet")


if __name__ == "__main__":
    main()
