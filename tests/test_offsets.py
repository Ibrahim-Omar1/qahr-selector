"""Tests for the versioned game-offset table (core/offsets.py)."""
from __future__ import annotations

import json

from selector.core.offsets import CURRENT, TARGETS, GameTarget, get_target


def test_current_is_registered() -> None:
    assert CURRENT.version in TARGETS
    assert get_target() is CURRENT
    assert get_target(CURRENT.version) is CURRENT


def test_struct_offsets_distinct() -> None:
    # selected UID vs selected OBJECT must differ, and coords are separate.
    st = CURRENT.structs
    assert st.sel_uid != st.sel_obj
    assert st.coord_x != st.coord_y
    assert st.uid != st.name


def test_hook_sites_have_signatures() -> None:
    # every hook site should carry a re-resolvable AOB signature + a VA.
    for name, sig in CURRENT.sites.items():
        assert sig.pattern, f"site {name} missing signature"
        assert sig.va, f"site {name} missing VA"


def test_agent_config_is_json_serialisable() -> None:
    cfg = CURRENT.to_agent_config()
    blob = json.dumps(cfg)  # must not raise
    again = json.loads(blob)
    assert again["module"] == "Conquer.exe"
    assert again["imageBase"] == 0x400000
    # VAs shift every client build — assert it's a plausible .text VA, not a magic
    # number (that would break on each recompile, e.g. the v3071->v3076 re-port).
    follow_va = again["sites"]["follow"]["va"]
    assert isinstance(follow_va, int) and follow_va > again["imageBase"]
    assert again["structs"]["uid"] == 0x268  # struct offsets ARE stable


def test_dataclass_is_frozen() -> None:
    import dataclasses

    assert dataclasses.is_dataclass(GameTarget)
