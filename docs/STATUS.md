# Status & Roadmap

What's actually built and verified, vs. what's next. Built one feature at a time.

## Verified working (live)
| Capability | How | Risk |
|-----------|-----|------|
| **Attach + hero read** | `MemoryReader.hero()` — pymem, `[heroSlot]` | read-only, none |
| **ESP / radar** | `MemoryReader.entities()` — scene-roster walk (see [ESP.md](ESP.md)) | read-only, none |
| **Guilds & relations** | guild name/id + ally/enemy/guildmate coloring from your in-game relations (see [GUILDS.md](GUILDS.md)) | read-only, none |
| **UI (Fluent dark)** | app shell + radar page (minimap + table), collapsible icon sidebar, Mock⇄Live toggle (`uv run selector`) | read-only, none |
| **Auto-HP** | toggle + "drink below %" that writes the game's native auto-pot settings (see [AUTO.md](AUTO.md)) | low-risk settings write |
| **Per-frame game-thread tick** | Frida agent hooks `user32!PeekMessageW` (`scripts/prove_tick.py`) | read-only proof; foundation for drivers |
| **Observability** | loguru + faulthandler + frida detach/error wiring + watchdog (`services/observability.py`) | — |

## Foundation in place
- `core/offsets.py` — single-source `GameTarget` (structs, roster, globals, functions,
  sites) with AOB signatures for version-robust re-resolution.
- `core/models.py` — `Hero`, `Entity`, `EntityKind`, `Relation`; `core/radar.py` —
  pure helpers (`classify`, `relation`, distance).
- `engine/` — `EngineProtocol`, `MemoryReader` (pymem), `MockEngine` (no-game),
  `FridaSession` + `agent/conquer.js` (read-only tick).
- `ui/` — Fluent-dark theme, widgets (minimap, entity table), pages; `viewmodels/`
  (`RadarViewModel`); `app/bootstrap.py` composition root.
- Tooling: uv · ruff · mypy(strict) · pytest (24 green). See [DEVELOPMENT.md](DEVELOPMENT.md).

## Pending / next
| Item | Notes |
|------|-------|
| **`selected_uid` (read-only)** | No static global exists — needs the low-freq SELECT hook or a differential heap scan. Unblocks ESP `TARGET` marking. See the dead-end in [MEMORY_MAP.md](MEMORY_MAP.md#selected-target--no-read-only-source-known-dead-end). |
| **Auto-Mana (idle)** | The game's native MP auto-pot only runs **while Auto-Hunt is hunting** + its threshold isn't a plain field, so idle Auto-Mana needs the active `UsageFunc`-from-tick path. Deferred. |
| **Combat (act on relation)** | Use `Entity.relation` to drive actions: attack enemies, never hit allies/guildmates. The relation data is already live; this is the first feature to consume it. |
| **`follow` (driver)** | First feature that *calls* a game function (`SentFunc`→`JumpFunc`) from the tick. Plan: single-call gate first, then loop. Builds the SELECT hook (which also gives `selected_uid`). |

## Known dead-ends (don't re-chase)
- `[0x1A0D628]`, `[camSlot]+0x11208`, `sentGetter` for selected target — all ruled out
  read-only (see MEMORY_MAP).
- `entity+0x11B8` / `0xFD6C8E` is a visual-effect render loop, **not** the entity list.
- frida **17.10.0** fails to inject into the 32-bit client; pinned to **17.7.3**.
