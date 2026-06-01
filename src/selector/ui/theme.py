"""ui/theme — the design system (tokens + global stylesheet).

A **Windows 11 / Fluent dark** palette: layered neutral grays (Mica-style, not
harsh black — comfortable for long sessions), a Win11 blue accent, Segoe UI
Variable, rounded Fluent controls. Pure data + a QSS builder (no widgets), so
the entity colors here are shared by both the table and the minimap.
"""
from __future__ import annotations

from dataclasses import dataclass

from selector.core.models import EntityKind


@dataclass(frozen=True)
class Palette:
    """Color tokens (hex or rgba() strings, QSS-ready)."""

    # Fluent dark "Mica" layering: base -> layer -> control, all neutral grays.
    bg: str = "#202020"                          # window base (Mica approx)
    surface: str = "#272727"                     # nav pane / sidebar layer
    card: str = "#2B2B2B"                         # cards / panels (layer fill)
    elevated: str = "#323232"                     # controls / hover fill
    border: str = "rgba(255,255,255,0.08)"        # card/control stroke
    border_soft: str = "rgba(255,255,255,0.05)"
    divider: str = "rgba(255,255,255,0.06)"

    text: str = "#FFFFFF"
    muted: str = "rgba(255,255,255,0.78)"         # secondary text
    faint: str = "rgba(255,255,255,0.40)"         # tertiary / disabled

    accent: str = "#4CC2FF"                        # Win11 dark accent (blue)
    accent_hover: str = "#3AA9E0"
    on_accent: str = "#00263D"                     # dark text on accent fill
    danger: str = "#FF7B72"
    warn: str = "#FFD166"

    # entity-kind colors (shared by table + minimap)
    self_: str = "#4CC2FF"
    player: str = "#6CB8FF"
    monster: str = "#FF7B72"
    npc: str = "#A9B2BD"
    target: str = "#FFD166"


@dataclass(frozen=True)
class Metrics:
    """Spacing / radius / sizing scale (px) — Fluent-ish."""

    pad_s: int = 4
    pad: int = 8
    pad_l: int = 16
    pad_xl: int = 24
    radius: int = 8          # cards / buttons
    radius_s: int = 5        # nav items / small controls
    sidebar_w: int = 200
    header_h: int = 52
    font_ui: str = '"Segoe UI Variable", "Segoe UI"'
    font_mono: str = '"Cascadia Mono", "Consolas", monospace'


COLORS = Palette()
METRICS = Metrics()

_KIND_COLOR: dict[EntityKind, str] = {
    EntityKind.SELF: COLORS.self_,
    EntityKind.PLAYER: COLORS.player,
    EntityKind.MONSTER: COLORS.monster,
    EntityKind.NPC: COLORS.npc,
    EntityKind.TARGET: COLORS.target,
}


def kind_color(kind: EntityKind) -> str:
    """Hex color for an entity kind (consistent across table + minimap)."""
    return _KIND_COLOR.get(kind, COLORS.npc)


def qss() -> str:
    """Global Qt stylesheet built from the tokens (Fluent dark)."""
    c, m = COLORS, METRICS
    return f"""
    * {{
        font-family: {m.font_ui};
        font-size: 13px;
        color: {c.text};
        outline: none;
    }}
    QWidget#root, QMainWindow {{ background: {c.bg}; }}

    /* sidebar (NavigationView pane) */
    QWidget#sidebar {{ background: {c.surface}; }}
    QLabel#brand {{ font-size: 17px; font-weight: 700; color: {c.text}; }}
    QLabel#brandAccent {{ font-size: 17px; font-weight: 700; color: {c.accent}; }}
    QLabel#navHint {{ color: {c.faint}; font-size: 11px; }}
    QPushButton#nav {{
        text-align: left; padding: 9px 12px 9px 14px; border: none;
        border-left: 3px solid transparent; border-radius: {m.radius_s}px;
        color: {c.muted}; background: transparent; font-weight: 600;
    }}
    QPushButton#nav:hover {{ background: {c.divider}; color: {c.text}; }}
    QPushButton#nav:checked {{
        background: {c.elevated}; color: {c.text}; border-left: 3px solid {c.accent};
    }}
    QPushButton#nav:disabled {{ color: {c.faint}; }}

    /* header */
    QWidget#header {{ background: {c.bg}; border-bottom: 1px solid {c.divider}; }}
    QLabel#pageTitle {{ font-size: 18px; font-weight: 700; }}
    QLabel#muted {{ color: {c.muted}; }}
    QLabel#mono {{ font-family: {m.font_mono}; color: {c.text}; }}

    /* status pill */
    QLabel#pill {{
        background: {c.elevated}; border: 1px solid {c.border};
        border-radius: 11px; padding: 3px 10px; color: {c.muted}; font-weight: 600;
    }}

    /* cards / panels */
    QFrame#card {{
        background: {c.card}; border: 1px solid {c.border}; border-radius: {m.radius}px;
    }}
    QLabel#cardTitle {{ color: {c.muted}; font-weight: 700; font-size: 11px; letter-spacing: 1px; }}

    /* table */
    QTableView {{
        background: transparent; border: none; gridline-color: {c.border_soft};
        selection-background-color: {c.divider}; selection-color: {c.text};
    }}
    QHeaderView::section {{
        background: transparent; color: {c.muted}; border: none;
        border-bottom: 1px solid {c.border}; padding: 7px 8px; font-weight: 600;
    }}
    QTableView::item {{ padding: 5px 8px; border: none; }}

    /* Fluent segmented toggle (Mock/Live) */
    QPushButton#toggle {{
        background: {c.elevated}; border: 1px solid {c.border}; border-radius: {m.radius_s}px;
        padding: 6px 14px; color: {c.muted}; font-weight: 600;
    }}
    QPushButton#toggle:hover {{ background: {c.divider}; color: {c.text}; }}
    QPushButton#toggle:checked {{
        background: {c.accent}; border-color: {c.accent}; color: {c.on_accent};
    }}

    /* sliders (radius) */
    QSlider::groove:horizontal {{ height: 4px; background: {c.elevated}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: {c.accent}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        background: {c.text}; width: 14px; height: 14px; margin: -6px 0; border-radius: 7px;
    }}

    /* scrollbars */
    QSplitter::handle {{ background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {c.border}; border-radius: 5px; min-height: 28px; }}
    QScrollBar::handle:vertical:hover {{ background: {c.faint}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    """
