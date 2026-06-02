r"""
core/offsets.py — the SINGLE source of truth for every game address/offset.

Why this file exists
--------------------
Conquer is recompiled every client build, so absolute addresses (VAs) shift.
The version-robust way to survive that (see Guided Hacking / jakob.space) is to
store **AOB signatures** — byte patterns with ``??`` wildcards over the volatile
bytes (relative addresses) — and resolve the real address at runtime by scanning
the module.  Struct field offsets, by contrast, are stable across minor builds.

A ``GameTarget`` carries:
  * ``structs``   — entity/hero field offsets (stable; rarely change)
  * ``globals``   — absolute VA slots holding live pointers (per-build)
  * ``functions`` — internal functions to call (VA + optional signature)
  * ``sites``     — inline-hook locations (VA + signature; signature preferred)

To port to a NEW client version:
  1. copy the ``V3076`` block to a new ``GameTarget``,
  2. update only the signatures if a major/obfuscated update broke them (they
     usually survive — that's the point), and bump ``CURRENT``.

Nothing here imports Qt/Frida/pymem — it's plain data, serialisable to the JSON
config injected into the Frida agent (``to_agent_config``).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sig:
    """A code address located by an AOB signature (preferred) and/or a known VA.

    pattern : CE-style byte pattern, e.g. "8B 8E F8 0A 00 00 3B" with "??" for
              volatile bytes.  None -> resolve by VA only.
    va      : absolute VA for THIS build (ImageBase-based). Fallback + sanity
              check against the scan result.
    note    : human description of the site/function.
    """

    pattern: str | None = None
    va: int | None = None
    note: str = ""


@dataclass(frozen=True)
class StructOffsets:
    """Entity / hero object field offsets (stable across minor builds)."""

    uid: int = 0x268          # entity UID
    name: int = 0x2A0         # CString ptr -> UTF-16LE display name
    coord_sub: int = 0x770    # coord subobject ptr
    coord_x: int = 0x10       # subobj + this >> shift = tile X
    coord_y: int = 0x14       # subobj + this >> shift = tile Y
    coord_shift: int = 6
    pk: int = 0x1B7C          # PK-mode enum
    syndicate_id: int = 0xB40    # guild/syndicate id (0 = not in a guild)
    syndicate_rank: int = 0xB44  # rank/position within the guild
    syndicate_name: int = 0xB70  # std::wstring guild name (SSO-aware; len @ +0x10)
    speed: int = 0x3F0        # move-speed
    magic_cd: int = 0x1DBC    # magic-cooldown gate
    anim: int = 0x3D8         # action/animation id
    swing_clock: int = 0x730  # action-start ms (attack pacing)
    follow_tgt: int = 0xAF8   # follow/interaction target id + range clamp
    last_x: int = 0x4FF0      # cached last tile X (walk dedup)
    last_y: int = 0x4FF4
    autohp_flag: int = 0x4ED4  # AutoHP branch byte
    # Native auto-HP-pot (drive the game's own potion use; verified live):
    autopot_hp_enable: int = 0x4EC8  # hero byte: 1 = HP-pot enabled (idle path)
    autopot_hp_pct: int = 0x4ED0     # hero dword: HP% threshold (cadence path)
    ninja_hp_pct: int = 0x154        # [ninjaSkillMgr]+0x154 HP% threshold (main path)
    # scene-object fields (the object esi points to at the SELECT site):
    sel_uid: int = 0x11208    # scene + this = selected target UID
    sel_obj: int = 0x1120C    # scene + this = selected target OBJECT ptr (unverified)


@dataclass(frozen=True)
class RosterLayout:
    """The scene's visible-entity collection (read-only enumeration source).

    An inline object at the static VA ``container``; its entity storage is an
    MSVC ``std::deque<element>`` where each element is 8 bytes
    ``{entity_ptr, _extra}`` (so 2 elements per 16-byte block). Walk live:

        count   = [container + count]
        _Map    = [container + map_ptr]      # T** block array
        _Mapsize= [container + map_size]
        _Myoff  = [container + front_off]    # MOVES as entities spawn/despawn
        for i in range(count):
            g     = _Myoff + i
            block = [_Map + ((g // block_elems) % _Mapsize) * 4]
            ent   = [block + (g % block_elems) * elem_size]

    Verified live (v3071): walking it recovers every nearby player/monster/NPC
    with matching ``+0x268`` uid and ``+0x770`` coords. Zero injection.
    """

    container: int = 0x1A0F488   # inline scene roster (static VA)
    map_ptr: int = 0x18          # +0x18 -> deque _Map (T** blocks)
    map_size: int = 0x1C         # +0x1C -> deque _Mapsize
    front_off: int = 0x20        # +0x20 -> deque _Myoff (front offset; live)
    count: int = 0x24            # +0x24 -> element count
    block_elems: int = 2         # MSVC _DEQUESIZ for 8-byte elements
    elem_size: int = 8           # element = {entity_ptr@+0, _extra@+4}
    # Syndicate-relation table (same singleton): vector<CSyndicateEntry*>.
    rel_begin: int = 0x58        # +0x58 -> begin ptr
    rel_end: int = 0x5C          # +0x5C -> end ptr
    rel_id: int = 0x08           # entry +0x08 -> syndicate id
    rel_value: int = 0x3C        # entry +0x3C -> 0=ally, 1=enemy, 2=own (verified live)
    rel_name: int = 0x24         # entry +0x24 -> guild name (std::wstring)


@dataclass(frozen=True)
class GameTarget:
    """A complete, version-pinned description of one Conquer client build."""

    version: str
    module: str
    image_base: int
    md5: str
    structs: StructOffsets
    roster: RosterLayout         # scene visible-entity collection (read-only)
    globals: dict[str, int]      # name -> absolute VA slot (holds a pointer)
    functions: dict[str, Sig]    # name -> callable internal function
    sites: dict[str, Sig]        # name -> inline-hook site

    def to_agent_config(self) -> dict[str, object]:
        """Plain JSON-able dict injected into the Frida agent.

        Keys are camelCase to read naturally in JS; the agent resolves each
        site/function by signature (preferred) then VA.
        """

        def sig(s: Sig) -> dict[str, object]:
            return {"pattern": s.pattern, "va": s.va, "note": s.note}

        st = self.structs
        return {
            "version": self.version,
            "module": self.module,
            "imageBase": self.image_base,
            "structs": {
                "uid": st.uid, "name": st.name,
                "coordSub": st.coord_sub, "coordX": st.coord_x,
                "coordY": st.coord_y, "coordShift": st.coord_shift,
                "pk": st.pk, "speed": st.speed, "magicCd": st.magic_cd,
                "anim": st.anim, "swingClock": st.swing_clock,
                "followTgt": st.follow_tgt, "lastX": st.last_x,
                "lastY": st.last_y, "autohpFlag": st.autohp_flag,
                "selUid": st.sel_uid, "selObj": st.sel_obj,
            },
            "globals": dict(self.globals),
            "functions": {k: sig(v) for k, v in self.functions.items()},
            "sites": {k: sig(v) for k, v in self.sites.items()},
        }


# --------------------------------------------------------------------------- #
# v3076 — current target (md5 87965DF398918B55B76B6FE5664B8965, ImageBase 0x400000).
#   Conquer.exe+OFFSET == VA - 0x400000.  Globals re-derived live for v3076
#   (recompile of v3071); struct offsets + roster/relation layout are unchanged.
#   Sites re-resolve from their AOB signatures; functions VAs are stale v3071
#   (used only by unbuilt active features — re-derive before use).
# --------------------------------------------------------------------------- #
V3076 = GameTarget(
    version="v3076",
    module="Conquer.exe",
    image_base=0x400000,
    md5="87965DF398918B55B76B6FE5664B8965",
    structs=StructOffsets(),
    roster=RosterLayout(container=0x1A20D78),   # v3071 0x1A0F488
    globals={
        "heroSlot": 0x1A170A0,       # v3071 0x1A057C0 — [heroSlot] -> local player
        "ninjaSkillMgr": 0x1A171C4,  # v3071 0x1A058E4 — auto-hunt/auto-pot mgr
        "camSlot": 0x1A16DD8,        # v3071 0x1A054F8 — scene/camera object
        "blessedTid": 0x1A10A14,     # v3071 VA — STALE; re-derive before active calls
        # std::vector<uint32> of monster UIDs (begin/end) — authoritative monster set.
        "monsterVecBegin": 0x1A20EA0,  # v3071 0x1A0F5B0
        "monsterVecEnd": 0x1A20EA4,    # v3071 0x1A0F5B4
    },
    functions={
        # NOTE: VAs below are v3071 and STALE on v3076 — re-derive before calling
        # (none are used by the current read/write-only features).
        "sentGetter": Sig(None, 0x43C68C, "hero/scene getter -> [heroSlot]"),
        "jump": Sig(None, 0x10F2074, "JumpFunc thiscall(this,X,Y) ret 8"),
        "walkXY": Sig(None, 0x111267C, "walk to X,Y"),
        "runBabyrun": Sig(None, 0x10D275D, "run"),
        "steedWalk": Sig(None, 0x11217F3, "mounted move"),
        "meleeSent1": Sig(None, 0xF05901, "melee chain 1"),
        "meleeFunc": Sig(None, 0xF13BE8, "melee build (MsgAction 0x838)"),
        "meleeSent2": Sig(None, 0xF44AF6, "melee chain 2 (sign/seq/send)"),
        "idSkill": Sig(None, 0x11857E8, "cast skill by target id"),
        "xySkill": Sig(None, 0x1186E22, "cast skill at X,Y"),
        "usage": Sig(None, 0xFE22C0, "use item by template id"),
        "revive": Sig(None, 0xEAAD2B, "revive entry"),
    },
    sites={
        # select sig no longer matches on v3076 (re-find); VA stale. follow/entIter
        # re-resolved live by their signatures.
        "select": Sig("89 86 08 12 01 00 E8", 0x4D79FB,
                      "mov [esi+0x11208],eax - esi=scene, eax=selected UID (STALE)"),
        "follow": Sig("8B 8E F8 0A 00 00 3B", 0xFB4833,
                      "mov ecx,[esi+0xAF8] - per-frame hero re-entry"),
        "entIter": Sig("8B 90 68 02 00 00 8D", 0xDD809E,
                       "mov edx,[eax+0x268] - per-entity iteration (ESP/SXYE)"),
    },
)


# Registry + the build the app currently targets.
TARGETS: dict[str, GameTarget] = {V3076.version: V3076}
CURRENT: GameTarget = V3076


def get_target(version: str | None = None) -> GameTarget:
    """Return the GameTarget for ``version`` (default: ``CURRENT``)."""
    if version is None:
        return CURRENT
    return TARGETS[version]
