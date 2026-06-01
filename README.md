# Selector

A clean, modern desktop trainer for **Qahr Online (Conquer Online v3071)** —
**gameplay only**, no DRM / HWID / telemetry.

- **UI:** PySide6 (MVVM)
- **Memory:** pymem
- **Hooks / game-function calls:** Frida (agent + RPC)
- **Tooling:** uv · ruff · mypy · pytest · PyInstaller

See `ARCHITECTURE.md` for the design. Built one feature at a time.

## Dev setup
```sh
uv sync --extra dev          # create venv + install deps
uv run selector              # run the app
uv run ruff check . && uv run mypy src && uv run pytest
```

> Status: scaffolding. The first milestone is proving the per-frame game-thread
> tick, then the `follow` feature end-to-end.
