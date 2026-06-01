# Selector

A clean, modern desktop trainer for **Qahr Online (Conquer Online v3071)**.
**Gameplay/QoL only** — no DRM, HWID, or telemetry code.

| | |
|---|---|
| **UI** | PySide6 (MVVM) — *deferred, in design* |
| **Memory** | pymem (read-only state) |
| **Hooks / game-function calls** | Frida (agent + RPC) |
| **Tooling** | uv · ruff · mypy (strict) · pytest · PyInstaller |

Built **one feature at a time**, library-first (no hand-written caves/assembler).
The old hand-rolled tools and the Cheat Engine table are treated as an
offset/logic **spec only** — never copied as code.

## Why it doesn't crash the game
Inline-hooking gameplay code froze/closed the client. Instead: **one per-frame
tick on the game thread** (hook a system function the message loop calls every
frame), run feature *drivers* from it (they *call* the game's own functions —
tripwire-safe), keep **read-only state in pure pymem** (zero injection), and use
a **single low-frequency SELECT hook** for the clicked target. See
[ARCHITECTURE.md](ARCHITECTURE.md).

## Status
Verified live, **read-only (zero injection)**:

| Feature | State |
|---------|-------|
| Attach + hero read (uid, name, coords, pk, speed) | ✅ working |
| **ESP / radar** — nearby players/monsters/NPCs with name, coords, kind, distance | ✅ working |
| Per-frame game-thread tick (Frida `PeekMessageW`) | ✅ proven |
| Observability (loguru + faulthandler + frida wiring + watchdog) | ✅ |
| `selected_uid` (read-only) | ⛔ no static global — needs the SELECT hook |
| `follow` driver | ⏳ next |
| UI | ⏳ deferred (discuss redesign first) |

Details + roadmap: **[docs/STATUS.md](docs/STATUS.md)**.

## Quickstart
```sh
uv sync --extra dev                      # create .venv + install deps
uv run ruff check . && uv run mypy src && uv run pytest
```
Run against the live game (in-world):
```sh
uv run python scripts/esp_dump.py        # read-only ESP/radar dump
uv run python scripts/prove_tick.py      # read-only Frida tick proof
```
If `uv` isn't on PATH, the venv tools work directly — see
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Layout
```
src/selector/
├── core/      # pure domain: offsets (single source), models, radar logic
├── engine/    # I/O: pymem reads, frida session, agent/*.js, mock engine
├── services/  # observability (logging/crash/watchdog), fleet mgr
├── viewmodels/ ui/   # MVVM + PySide6 (deferred)
scripts/       # read-only runners (esp_dump, prove_tick)
tests/         # no-game pytest (offsets, radar, engine, observability)
docs/          # reference docs (below)
```

## Docs
- **[docs/STATUS.md](docs/STATUS.md)** — what works vs pending, and known dead-ends
- **[docs/MEMORY_MAP.md](docs/MEMORY_MAP.md)** — verified addresses/offsets (mirrors `core/offsets.py`)
- **[docs/ESP.md](docs/ESP.md)** — the read-only radar: roster walk + usage
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** — setup, gates, live-testing, gotchas
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — layered/MVVM design + the tick/driver pivot

## Notes
- `core/offsets.py` is the single source for every address/offset (AOB signatures
  let them re-resolve across client rebuilds).
- **frida is pinned to `17.7.3`** — `17.10.0` fails to inject into the 32-bit client.
- For authorized private-server / testing use only.
