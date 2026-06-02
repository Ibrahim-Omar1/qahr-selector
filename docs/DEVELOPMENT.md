# Development

## Setup
```sh
uv sync --extra dev          # create .venv + install runtime + dev deps
```
- Python is pinned via `.python-version` (3.12); the floor is 3.10 (`requires-python`).
- Deps are locked in `uv.lock`. **frida is pinned to `17.7.3`** — `17.10.0` fails to
  inject into the 32-bit client ("refused to load frida-agent").

## The gates (must stay green)
```sh
uv run ruff check .          # lint + import order (E,F,I,UP,B,SIM)
uv run mypy src              # strict
uv run pytest -q             # no-game tests
```

### If `uv` isn't on PATH
Some shells don't have `uv` exported. The venv tools work directly:
```powershell
$s = ".venv\Scripts"
& "$s\ruff.exe" check . ; & "$s\mypy.exe" src ; & "$s\pytest.exe" -q
```

## Run the app
```powershell
uv run selector                       # GUI on Mock data (no game needed)
uv run selector --live                # attach to the live game (read-only)
# uv not on PATH? the installed console script works:
.venv\Scripts\selector.exe --live
```
The Mock⇄Live toggle in the header switches engines at runtime — no restart.

## Running scripts against the live game
Scripts read `src/` via the package; set `PYTHONPATH=src` (or use `uv run`):
```powershell
$env:PYTHONPATH = "src"
.venv\Scripts\python.exe scripts\esp_dump.py        # read-only radar dump
.venv\Scripts\python.exe scripts\prove_tick.py      # read-only frida tick proof
```
- `esp_dump.py` / hero reads: pure pymem, safe at any game state.
- `prove_tick.py`: injects the read-only Frida agent (tolerated; clean detach).

## Live-testing approach
- **Read-only first.** Verify every new offset/path against the running game with a
  throwaway probe before wiring it into the engine. Cross-check decoded values
  (uid/coords/name) against what's on screen.
- **Self-validate reads.** When resolving via a chain, confirm `[obj+0x268]` matches an
  expected uid before trusting coords — catches a wrong base immediately (that's how the
  bad `selected_uid` base was caught).
- **Anything that hooks or calls game code** follows ARCHITECTURE.md: drive from the
  per-frame tick, never inline-hook a hot site, single-call gate before looping, watch
  the observability detach log.

## Gotchas
- In PowerShell, a Python helper named `rd(` trips a shell guard (`rd` = Remove-Item
  alias) — name probe helpers `deref`/`u32` instead.
- Console can't print Arabic by default; `esp_dump.py` reconfigures stdout to UTF-8.
- `reference/` (the original CT) is gitignored — it's a spec, not shipped code.

## Layout
See [../ARCHITECTURE.md](../ARCHITECTURE.md). `core` is pure (no Qt/frida/pymem) and
unit-tested without the game; `engine` holds all the I/O.
