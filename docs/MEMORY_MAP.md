# Memory Map — Conquer v3071

Verified addresses/offsets for the live v3071 client. **`core/offsets.py` is the
single source of truth** — this doc is the human-readable mirror. If they disagree,
`offsets.py` wins (update this doc).

- **Module:** `Conquer.exe` · **ImageBase:** `0x400000` (no ASLR observed)
- **Rebase:** `live = module_base + (VA - 0x400000)` (`MemoryReader._rebase`)
- **md5:** `A671CD3A`
- Coords are tile units: a coord subobject holds raw `X/Y`; `tile = raw >> 6`.

## Globals (`offsets.globals`)
| Name | VA | Meaning |
|------|----|---------|
| `heroSlot` | `0x1A057C0` | `[heroSlot]` → local player object |
| `camSlot` | `0x1A054F8` | `[camSlot]` → scene/camera object |
| `monsterVecBegin` / `monsterVecEnd` | `0x1A0F5B0` / `0x1A0F5B4` | `std::vector<u32>` of monster UIDs (authoritative monster set) |
| `blessedTid` | `0x1A10A14` | thread-identity tripwire (relevant only to injected/called paths) |

## Entity / hero struct fields (`StructOffsets`)
Same object layout for the hero and every roster entity.

| Offset | Field | Notes |
|--------|-------|-------|
| `+0x268` | UID | `> 0xF423F` (999999) ⇒ player; else monster/NPC |
| `+0x2A0` | name | pointer → UTF-16LE string |
| `+0x770` | coord subobj | `X = [+0x10] >> 6`, `Y = [+0x14] >> 6` |
| `+0x870` | classify byte | weak signal; prefer the monster vector |
| `+0x1B7C` | PK mode | `0` Free · `1` Peace · `2` Team · `3` Capture · `4` Guild · `5` Ally |
| `+0xB40` | syndicate (guild) id | `0` = not in a guild; gate the name read on this |
| `+0xB44` | syndicate rank/position | |
| `+0xB70` | guild name | **`std::wstring` (SSO-aware)** — short names (`RoD`, `حبوبه`) inline, long ones heap; len at `+0xB80`. Gate on `+0xB40 != 0`. |
| `+0xAC0` | mate/spouse name | CString ptr → UTF-16; `NOMATE_NAME@@` when single |
| `+0x3F0` | move speed | |
| `+0xAF8` | follow/interaction target id **and** range clamp | context-dependent (NOT mana) |

## Scene entity roster — read-only radar source (`RosterLayout`)
Static inline object at **`0x1A0F488`**. Entity storage is an MSVC `std::deque` of
**8-byte elements `{entity_ptr@+0, _extra@+4}`** (2 per block). The local hero is *not*
in this roster (it's the `heroSlot` singleton).

| Container offset | Field |
|------------------|-------|
| `+0x18` | deque `_Map` (T** block array) |
| `+0x1C` | deque `_Mapsize` |
| `+0x20` | deque `_Myoff` (front offset — **moves as entities spawn/despawn; read live**) |
| `+0x24` | element count |
| `+0x28` | rb-tree header (UID → deque-index map; node `+0x10` uid, `+0x14` idx) |

**Walk** (i = 0 … count-1):
```
g     = _Myoff + i
block = [ _Map + ((g // 2) % _Mapsize) * 4 ]
ent   = [ block + (g % 2) * 8 ]
```
Implemented in `MemoryReader.entities()`. Verified live: recovers every nearby
player/monster/NPC with matching uid + coords + name. See [ESP.md](ESP.md).

> **Correction:** `entity+0x11B8` / `0xFD6C8E` (called a "visible-entity container"
> in the RE project's `SELECTOR_CT_ANALYSIS.md`) is actually a per-entity *visual-effect*
> render loop — NOT the entity list. The roster above is the real one.

## Internal functions (`offsets.functions`) — for later driver/hook features
| Name | VA | Convention |
|------|----|-----------|
| `sentGetter` | `0x43C68C` | `() → [heroSlot]` (lazy-inits hero) |
| `jump` | `0x10F2074` | thiscall `(this, X, Y)`, `ret 8` |
| `walkXY` | `0x111267C` | walk to X,Y |
| `idSkill` / `xySkill` | `0x11857E8` / `0x1186E22` | cast by target-id / at X,Y |
| `meleeSent1`/`meleeFunc`/`meleeSent2` | `0xF05901`/`0xF13BE8`/`0xF44AF6` | melee chain |
| `usage` | `0xFE22C0` | use item by template id |
| `revive` | `0xEAAD2B` | revive entry |

## Inline-hook sites (`offsets.sites`) — signatures preferred (version-robust)
| Name | Signature | VA | Use |
|------|-----------|----|-----|
| `select` | `89 86 08 12 01 00 E8` | `0x4D79FB` | SELECT write (`eax` = clicked UID, `[ebp+8]` = target obj) |
| `follow` | `8B 8E F8 0A 00 00 3B` | `0xFAC595` | per-frame hero re-entry (CT's follow site) |
| `entIter` | `8B 90 68 02 00 00 8D` | `0xDCEEDA` | per-entity iteration (hot — do **not** JS-hook) |

## Selected target — NO read-only source (known dead-end)
There is **no static global** holding the current selection (verified live):
`[0x1A0D628]` reads 0; `[camSlot]+0x11208` is a constant that does not track selection;
`sentGetter` returns the hero. The scene object the SELECT handler (`0x4D79FB`) writes
is heap-only. ⇒ `MemoryReader.selected_uid()` is honestly `None`; getting it needs the
**SELECT hook** (the CT's `[Selector]`) or a differential heap scan. ESP doesn't need it.
