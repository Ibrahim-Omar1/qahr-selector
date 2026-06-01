"""engine — INFRASTRUCTURE layer (adapters to the running game).

`pymem`-based reads, the Frida session + agent (`agent/*.js`) for hooks and
calling internal game functions, and a MockEngine for UI/dev without the game.
All sit behind a single `EngineProtocol` so they are swappable.
"""
