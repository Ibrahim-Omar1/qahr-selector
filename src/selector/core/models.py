"""core/models — plain value objects the engine produces and the UI consumes.

Pure data (no Qt / frida / pymem). PK-mode mapping lives here too since it's a
domain concept.
"""
from __future__ import annotations

from dataclasses import dataclass

# PK-mode enum at hero+0x1B7C (verified from the CT: 1=Peace, 3=Capture).
PK_NAMES: dict[int, str] = {
    0: "Free (PK)", 1: "Peace", 2: "Team", 3: "Capture", 4: "Guild", 5: "Ally",
}


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
    kind: str        # "player" | "monster" | "target"
    dist: int        # Chebyshev distance from the hero

    @property
    def pk_name(self) -> str | None:
        return pk_label(self.pk)
