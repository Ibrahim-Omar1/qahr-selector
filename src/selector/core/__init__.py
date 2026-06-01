"""core — DOMAIN layer (pure data; no Qt / frida / pymem).

The versioned game definition (`offsets`), plain models (Hero/Entity), and the
feature catalog. Everything the rest of the app needs to know *about the game*
lives here, so porting to a new client build is a one-file edit.
"""
