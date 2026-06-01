"""Tests for the engine read layer (mock + protocol conformance)."""
from __future__ import annotations

from selector.engine.memory import MemoryReader
from selector.engine.mock_engine import MockEngine
from selector.engine.protocol import EngineProtocol


def test_mock_conforms_to_protocol() -> None:
    assert isinstance(MockEngine(), EngineProtocol)


def test_memory_reader_conforms_to_protocol() -> None:
    assert isinstance(MemoryReader(), EngineProtocol)


def test_mock_reads() -> None:
    e = MockEngine()
    assert e.attach() is True
    assert e.attached() is True
    h = e.hero()
    assert h is not None and h.name == "DemoHero"
    assert isinstance(h.x, int) and isinstance(h.y, int)
    assert e.selected_uid() == 1007799
    ents = e.entities()
    assert len(ents) >= 1
    assert all(isinstance(en.dist, int) for en in ents)


def test_mock_detached_returns_none() -> None:
    e = MockEngine()
    assert e.hero() is None  # not attached yet
