# Selector — Architecture

Qahr Online (Conquer v3071) trainer. **Gameplay only** — no DRM/HWID/telemetry.

## Principles
- **Libraries, not hand-rolled internals.** `pymem` for memory, `frida` for hooks
  + calling game functions, `PySide6` for UI. No custom auto-assembler, no
  hand-written caves.
- **Layers depend downward only:** `ui → viewmodels → services → engine → core`.
  `core` is pure data (no Qt/frida/pymem).
- **One feature at a time.** A feature is a self-contained module added to a
  registry; nothing global changes when you add one.

## The pivot that avoids the crashes
Don't inline-hook gameplay sites (that froze/closed the game). Instead:
- **One per-frame tick on the game thread** — hook a function the game calls
  every frame (message-loop / D3D Present). From it we run feature *drivers* and
  render-free logic; calling internal functions here is tripwire-safe.
- **Driver features** (follow, auto-melee, auto-hp…): each frame, *call* the
  game's internal functions toward the target. No site hook.
- **One low-freq SELECT hook**: grab the selected target object at the click.
- **Gate features** (range/energy/cooldown/walk-dedup): plain byte patches via
  pymem (the RE project's verified patches). No cave.

## Layout (`src` layout)
```
src/selector/
├── __main__.py        # thin entry: args → bootstrap → run
├── app/               # composition root (DI / wiring)
├── core/              # DOMAIN (pure): offsets (versioned GameTarget), models, feature catalog
├── engine/            # INFRASTRUCTURE: pymem reads, frida session, agent/*.js, mock
│   └── agent/         #   Frida agent JS (the per-frame tick + hooks)
├── services/          # instance/fleet manager, MCP diagnostics server
├── viewmodels/        # MVVM: QObject bridges (engine state ↔ UI, signals/properties)
└── ui/                # PySide6 views + design system (theme)
tests/                 # pytest (engine logic, offsets, mock)
```

## Patterns
- **MVVM** — views bind to view-models (signals/`Property`); view-models call services.
- **`EngineProtocol`** (PEP 544) — Frida / Mock engines are swappable.
- **Feature registry** — features are metadata + a handler; UI renders the list generically.
- **Composition root** (`app/bootstrap.py`) — no globals; wired in one place.
- **Single-source offsets** — `core/offsets.py`; codegen emits the JSON the agent consumes.

## Stack
PySide6 · pymem · frida · uv (deps) · ruff + mypy + pytest · PyInstaller (build).
