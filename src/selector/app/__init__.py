"""app — composition root (dependency injection / wiring).

`bootstrap.py` builds the QApplication, picks the engine, constructs services +
view-models + the main window, and wires them. No globals; one place to wire.
"""
