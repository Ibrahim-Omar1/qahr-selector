# Guilds & Relations

The radar shows each player's **guild** (name + id) and their **relationship** to
you — guildmate, ally, enemy, or neutral — read **read‑only** from memory. It
mirrors your in‑game *guild relations* panel (علاقة النقابة), so it updates live
as those relations change. No tagging, no injection.

## What you see
- **Guild** + **GID** columns in the entity table.
- Color coding (table guild/GID cell + minimap dot):
  | Relation | Color | Meaning |
  |----------|-------|---------|
  | guildmate | 🟡 yellow `#FFD93D` | same guild as you |
  | ally | 🟢 green `#3DDC84` | an ally guild (your panel's ally side) |
  | enemy | 🔴 red `#FF5C5C` | an enemy guild (your panel's enemy side) |
  | self | violet (accent) | you (not shown in the radar list) |
  | neutral | normal | everyone else |

## How it works
Two pieces, both read straight from the entity / a game singleton:

**1. Per‑player guild (on the entity object)**
- `+0xB40` — syndicate (guild) **id** (`0` = not in a guild).
- `+0xB44` — rank/position.
- `+0xB70` — guild **name**, an MSVC `std::wstring` (small‑string‑optimized):
  short names (`RoD`, `حبوبه`) are stored **inline**, long ones on the **heap** —
  decode via `_wstr` (length at `+0xB80`). Reading it as a plain pointer was the
  original bug (garbage/CJK for short names).

**2. Your guild's relations (a game singleton)**
- Same object as the entity roster: `0x1A0F488`.
- `+0x58` / `+0x5C` — begin/end of a `std::vector<CSyndicateEntry*>`.
- Per entry: `+0x08` = guild id, `+0x24` = name (`std::wstring`), **`+0x3C` =
  relation: `0`=ally, `1`=enemy, `2`=own** (verified live against both pages of
  the in‑game panel; the static-analysis guess of 1=ally/2=enemy was wrong).
- Lookup fn: `CSyndicateMgr::GetRelationByID` @ `0xE903B8` (ecx = `0x1A0F488`).

**Classification precedence** (`core/radar.relation()`):
`SELF` (uid==hero) → `GUILDMATE` (`entity+0xB40 == hero+0xB40`) →
`ALLY`/`ENEMY` (from the relation table) → `NEUTRAL`.

## Code
- `engine/memory.py` — `_read_syndicate_relations()` (walks the table → ally/enemy
  id sets), `_wstr()` (SSO‑aware guild name), `_decode_entity()`.
- `core/radar.py` — `relation()` (pure; takes ally/enemy sets).
- `core/models.py` — `Relation` enum; `Entity.guild`, `Entity.guild_id`, `Entity.relation`.
- `ui/theme.py` — `relation_color()`; applied in `ui/widgets/minimap.py` + `entity_table.py`.
- Offsets live in `core/offsets.py` (`StructOffsets.syndicate_*`, `RosterLayout.rel_*`).

## Notes / limits
- Relations are **your** relations (the local player's). A guild not in your
  ally/enemy lists shows as neutral even if it's at war with someone else.
- The in‑memory table holds **all** entries at once (it isn't paginated like the
  UI), so both panel pages are covered.
- Future **combat** features read `Entity.relation` directly (e.g. *attack
  enemies, never hit allies/guildmates*).
