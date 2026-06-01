# Selector

A clean, modern desktop trainer for **Qahr Online (Conquer Online v3071)** —
**gameplay only**, no DRM / HWID / telemetry.

- **UI:** PySide6 (MVVM)
- **Memory:** pymem
- **Hooks / game-function calls:** Frida (agent + RPC)
- **Tooling:** uv · ruff · mypy · pytest · PyInstaller

Built one feature at a time. **Docs: [`docs/`](docs/README.md)** —
[STATUS](docs/STATUS.md) · [MEMORY_MAP](docs/MEMORY_MAP.md) · [ESP](docs/ESP.md) ·
[DEVELOPMENT](docs/DEVELOPMENT.md) · [ARCHITECTURE](ARCHITECTURE.md).

## Dev setup
```sh
uv sync --extra dev          # create venv + install deps
uv run ruff check . && uv run mypy src && uv run pytest
```

## Status
Verified live (read-only): **attach + hero read**, **ESP / radar**
(`scripts/esp_dump.py`), and the **per-frame game-thread tick** (`scripts/prove_tick.py`).
Next: `selected_uid` via the SELECT hook, then the `follow` driver. UI is deferred.
See [docs/STATUS.md](docs/STATUS.md).
