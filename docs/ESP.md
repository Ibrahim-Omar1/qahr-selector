# ESP / Radar (read-only)

Lists nearby entities — players, monsters, NPCs — with name, tile coords, kind, and
distance from the hero. **Pure pymem reads: no injection, no hooks, no game-function
calls** → zero anti-cheat exposure. (The old tool did this by hooking the hot SXYE
site via a native cave; this does it entirely read-only.)

## How it works
1. `MemoryReader.hero()` reads the local player (`[heroSlot]`) for the distance origin.
2. `entities(radius=64)` walks the **scene roster** at `0x1A0F488` (an MSVC deque —
   see [MEMORY_MAP.md](MEMORY_MAP.md#scene-entity-roster--read-only-radar-source-rosterlayout)),
   reading `_Myoff` live each call.
3. Each element's entity pointer is decoded into a typed `core.models.Entity`
   (`uid, name, x, y, pk, kind, dist`) by `_decode_entity`.
4. `core.radar.classify()` assigns the `EntityKind`:
   - `TARGET` if uid == selected (currently never, since `selected_uid` is `None` read-only)
   - `PLAYER` if uid `> 0xF423F`
   - `MONSTER` if uid ∈ the game's monster-UID vector (`[0x1A0F5B0]..[0x1A0F5B4]`)
   - else `NPC`
5. Results are filtered to `radius` (Chebyshev tiles) and sorted by distance.

Everything is defensive: a torn/zero pointer degrades to a skipped entry, never a
crash. The walk is bounded by `MAX_ENTITIES` so a garbage count can't spin.

## Run it
```sh
uv run python scripts/esp_dump.py [radius=32] [cycles=3]
# or, if uv isn't on PATH (see DEVELOPMENT.md):
.venv\Scripts\python.exe scripts\esp_dump.py 32 3
```
Game must be in-world. Prints the hero + radar each cycle and logs to `logs/`.
Example (live):
```
hero Sadistic (uid 1050859) @ (317,292) — 11 entities within 32 tiles
  player  uid=1010459  Badr^AutoSeller  ( 313, 291)  d=4   pk=Free (PK)
  npc     uid=23056    التاجر الرحالة    ( 305, 280)  d=12  pk=Free (PK)
  monster uid=435486   -                ( 318, 305)  d=13  pk=Free (PK)
```

## Notes / limits
- **Selected-target marking (`TARGET`) is unavailable read-only** — see the dead-end
  in [MEMORY_MAP.md](MEMORY_MAP.md#selected-target--no-read-only-source-known-dead-end).
- Some player names render as stylized/garbled glyphs — those players use fancy
  Unicode name fonts (normal in CO), not a decode bug.
- Pure-pymem reads can momentarily see a torn pointer mid-update; that entry is just
  skipped that frame.

## Code
`engine/memory.py` (`entities`, `_decode_entity`, `_roster_entity_ptr`,
`_read_uid_vector`) · `core/radar.py` (`classify`, `chebyshev`) ·
`core/models.py` (`Entity`, `EntityKind`) · `scripts/esp_dump.py` (runner).
Mock data for no-game dev/tests: `engine/mock_engine.py`.
