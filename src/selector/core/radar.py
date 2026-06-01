"""core/radar — pure, process-free radar logic (classification + distance).

No pymem / Qt / frida here: just arithmetic over plain ints so it is trivially
unit-testable without the game attached. ``engine`` reads raw memory and calls
these to turn it into ``Entity`` values.

UID bands are a game-universal convention (not per-build), verified from the
client: the split at ``0xF423F`` (999999) separates players (above) from
monsters/NPCs (below); see ``project/findings/SELECTOR_CT_ANALYSIS.md`` §"UID
bands". They live here as named constants rather than in ``offsets.py`` because
they are not addresses tied to a binary build.
"""
from __future__ import annotations

from selector.core.models import EntityKind, Relation

# --- UID bands (entity classification) --------------------------------------
# uid > 0xF423F (999999)  -> a player
# uid >= 500001           -> monster / pet / guard
# uid <  500001           -> stationary NPC (shop, quest, ...)
UID_PLAYER_MIN = 0xF4240   # 1_000_000; first player id (0xF423F is the last non-player)
UID_MONSTER_MIN = 500_001  # call/pet/guard band starts here; monsters sit above it


def classify(
    uid: int,
    *,
    selected_uid: int | None = None,
    hero_uid: int | None = None,
    monsters: frozenset[int] = frozenset(),
) -> EntityKind:
    """Classify an entity by its UID relative to the hero and selected target.

    Precedence: the local player is always ``SELF``; otherwise the currently
    selected target is ``TARGET``; players are identified by the verified
    ``> 0xF423F`` band; monster-vs-NPC is decided by the game's authoritative
    monster-UID set when supplied (UID bands are unreliable for that split),
    falling back to the band otherwise.
    """
    if hero_uid is not None and uid == hero_uid:
        return EntityKind.SELF
    if selected_uid and uid == selected_uid:
        return EntityKind.TARGET
    if uid >= UID_PLAYER_MIN:
        return EntityKind.PLAYER
    if uid in monsters or (not monsters and uid >= UID_MONSTER_MIN):
        return EntityKind.MONSTER
    return EntityKind.NPC


def relation(
    uid: int,
    syndicate_id: int,
    *,
    hero_uid: int | None = None,
    hero_syndicate_id: int = 0,
    allies: frozenset[int] = frozenset(),
    enemies: frozenset[int] = frozenset(),
) -> Relation:
    """A player's relationship to the hero, from syndicate (guild) ids.

    Guildmate = same non-zero syndicate as the hero. Ally/enemy come from the
    hero guild's alliance/enmity lists (passed in; empty until those are wired).
    """
    if hero_uid is not None and uid == hero_uid:
        return Relation.SELF
    if syndicate_id and syndicate_id == hero_syndicate_id:
        return Relation.GUILDMATE
    if syndicate_id and syndicate_id in allies:
        return Relation.ALLY
    if syndicate_id and syndicate_id in enemies:
        return Relation.ENEMY
    return Relation.NEUTRAL


def chebyshev(ax: int, ay: int, bx: int, by: int) -> int:
    """King-move (Chebyshev) tile distance between two points."""
    return max(abs(ax - bx), abs(ay - by))


def within_radius(ax: int, ay: int, bx: int, by: int, radius: int) -> bool:
    """True if ``(bx, by)`` is within ``radius`` tiles (Chebyshev) of ``(ax, ay)``."""
    return chebyshev(ax, ay, bx, by) <= radius
