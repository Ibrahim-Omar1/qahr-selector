"""core/models — plain value objects the engine produces and the UI consumes.

Pure data (no Qt / frida / pymem). PK-mode mapping lives here too since it's a
domain concept.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# PK-mode enum at hero+0x1B7C (verified from the CT: 1=Peace, 3=Capture).
PK_NAMES: dict[int, str] = {
    0: "Free (PK)", 1: "Peace", 2: "Team", 3: "Capture", 4: "Guild", 5: "Ally",
}


class EntityKind(str, Enum):
    """What a radar entity is, relative to the local player.

    A ``str`` enum so it serialises and compares as its plain value (e.g. for
    logs / the future UI) while staying exhaustively checkable. ``str, Enum`` is
    used over 3.11's ``StrEnum`` to keep the 3.10 floor (see pyproject).
    """

    SELF = "self"        # the local player
    PLAYER = "player"    # another player
    MONSTER = "monster"  # monster / pet / guard
    NPC = "npc"          # stationary NPC (shop, quest, etc.)
    TARGET = "target"    # the currently selected target (overrides the rest)


class Relation(str, Enum):
    """A player's relationship to the local hero (orthogonal to EntityKind)."""

    SELF = "self"
    GUILDMATE = "guild"   # same syndicate as the hero
    ALLY = "ally"         # hero's guild allies (reserved — needs alliance lists)
    ENEMY = "enemy"       # hero's guild enemies (reserved)
    NEUTRAL = "neutral"


def pk_label(pk: int | None) -> str | None:
    """PK-mode value -> human label; unknown -> 'Mode N' (never '?')."""
    if pk is None:
        return None
    return PK_NAMES.get(pk, f"Mode {pk}")


@dataclass(frozen=True, slots=True)
class Hero:
    """The local player's live state (a read-only snapshot)."""

    uid: int
    name: str
    x: int
    y: int
    pk: int | None
    speed: int | None

    @property
    def pk_name(self) -> str | None:
        return pk_label(self.pk)


@dataclass(frozen=True, slots=True)
class Entity:
    """A nearby entity (player/monster) for the radar/ESP."""

    uid: int
    name: str
    x: int
    y: int
    pk: int | None
    kind: EntityKind
    dist: int        # Chebyshev distance from the hero
    guild: str = ""  # guild/syndicate name ("" if not in one)
    guild_id: int = 0  # syndicate id (0 = not in a guild)
    relation: Relation = Relation.NEUTRAL  # vs. the hero (guildmate/ally/enemy)

    @property
    def pk_name(self) -> str | None:
        return pk_label(self.pk)
