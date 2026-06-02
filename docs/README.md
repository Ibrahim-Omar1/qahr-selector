# Selector — Docs

Reference docs for the Qahr Online (Conquer v3076) trainer. **Gameplay only.**

| Doc | What's in it |
|-----|--------------|
| [STATUS.md](STATUS.md) | Feature status & roadmap — what's verified working vs pending, and the known read-only dead-ends. **Start here.** |
| [MEMORY_MAP.md](MEMORY_MAP.md) | The verified memory map: hero, entity roster, struct fields, globals, internal functions. Mirrors `core/offsets.py` (the single source of truth). |
| [ESP.md](ESP.md) | The read-only ESP/radar: how the scene-roster walk works + how to run `esp_dump.py`. |
| [GUILDS.md](GUILDS.md) | Guild name/id + relationship (guildmate/ally/enemy) coloring, read from your in-game guild relations. |
| [AUTO.md](AUTO.md) | Auto-HP — drives the game's own auto-potion via a settings write (toggle + threshold). |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Setup, the gates (ruff/mypy/pytest), running scripts, live-testing, and gotchas (uv/PATH, frida pin). |
| [../ARCHITECTURE.md](../ARCHITECTURE.md) | The layered/MVVM design and the "tick + drivers, no inline hooks" pivot. |

**Ground rules** (see also the repo's CLAUDE.md):
- The old tools (`tools/selector_py`, `esp_dump_3071.py`) and the CT in `reference/`
  are an **offset/logic spec only** — never a code template. Write clean, typed code.
- `core/offsets.py` is the **single source** for every address/offset; nothing
  hard-codes a literal `0x…` elsewhere.
- Read-only (pymem) features carry zero injection risk; anything that hooks or
  calls game code follows the tick/driver rules in ARCHITECTURE.md.
