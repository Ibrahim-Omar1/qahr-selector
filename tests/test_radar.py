"""Unit tests for core.radar — pure, no game required."""
from __future__ import annotations

from selector.core.models import EntityKind, Relation
from selector.core.radar import (
    UID_MONSTER_MIN,
    UID_PLAYER_MIN,
    chebyshev,
    classify,
    relation,
    within_radius,
)


def test_relation() -> None:
    me = 1_050_859
    assert relation(me, 26, hero_uid=me, hero_syndicate_id=26) is Relation.SELF
    # same non-zero syndicate as hero -> guildmate
    assert relation(1_000_711, 26, hero_uid=me, hero_syndicate_id=26) is Relation.GUILDMATE
    # different/zero syndicate -> neutral unless in ally/enemy sets
    assert relation(1_000_711, 0, hero_uid=me, hero_syndicate_id=26) is Relation.NEUTRAL
    assert relation(1_000_711, 14, hero_uid=me, hero_syndicate_id=26) is Relation.NEUTRAL
    assert relation(1, 14, hero_syndicate_id=26, allies=frozenset({14})) is Relation.ALLY
    assert relation(1, 99, hero_syndicate_id=26, enemies=frozenset({99})) is Relation.ENEMY


def test_classify_uid_bands() -> None:
    assert classify(UID_PLAYER_MIN) is EntityKind.PLAYER
    assert classify(UID_PLAYER_MIN - 1) is EntityKind.MONSTER  # 0xF423F == last non-player
    assert classify(UID_MONSTER_MIN) is EntityKind.MONSTER
    assert classify(UID_MONSTER_MIN - 1) is EntityKind.NPC
    assert classify(1) is EntityKind.NPC


def test_classify_self_takes_precedence() -> None:
    # a player uid that is also the hero -> SELF, never PLAYER/TARGET
    assert classify(1_050_000, hero_uid=1_050_000) is EntityKind.SELF
    assert classify(1_050_000, selected_uid=1_050_000, hero_uid=1_050_000) is EntityKind.SELF


def test_classify_monster_set() -> None:
    # a sub-band uid (bands alone -> NPC) is MONSTER when in the game's monster set
    assert classify(435486, monsters=frozenset({435486})) is EntityKind.MONSTER
    assert classify(435486) is EntityKind.NPC  # no set -> band says NPC (<500001)
    # players always win, even if (wrongly) present in the monster set
    assert classify(1_050_000, monsters=frozenset({1_050_000})) is EntityKind.PLAYER


def test_classify_target() -> None:
    # selected target wins over its band (here a monster-band uid)
    assert classify(700_500, selected_uid=700_500) is EntityKind.TARGET
    # selected_uid of 0/None must not match a real uid
    assert classify(700_500, selected_uid=0) is EntityKind.MONSTER
    assert classify(700_500, selected_uid=None) is EntityKind.MONSTER


def test_chebyshev() -> None:
    assert chebyshev(300, 300, 300, 300) == 0
    assert chebyshev(300, 300, 304, 302) == 4  # max(4, 2)
    assert chebyshev(300, 300, 297, 310) == 10  # max(3, 10)


def test_within_radius() -> None:
    assert within_radius(300, 300, 305, 300, radius=5) is True
    assert within_radius(300, 300, 306, 300, radius=5) is False
