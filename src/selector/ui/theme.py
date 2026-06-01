"""ui/theme — the design system (tokens + global stylesheet).

A **Windows 11 / Fluent dark** system built on a *single* spacing scale, one
control height, and a clear 3-step surface hierarchy so every control lines up.
Pure data + a QSS builder (no widgets). Entity colors are shared by the table
and the minimap.
"""
from __future__ import annotations

from dataclasses import dataclass

from selector.core.models import EntityKind


@dataclass(frozen=True)
class Palette:
    """Color tokens (hex / rgba() strings, QSS-ready). 3 surface steps."""

    bg: str = "#1B1B1B"          # window base
    sidebar: str = "#1F1F1F"     # nav pane
    card: str = "#242424"        # panels
    control: str = "#2D2D2D"     # buttons / inputs
    control_hover: str = "#353535"
    control_down: str = "#2A2A2A"

    border: str = "rgba(255,255,255,0.08)"
    divider: str = "rgba(255,255,255,0.06)"

    text: str = "#FFFFFF"
    muted: str = "rgba(255,255,255,0.72)"
    faint: str = "rgba(255,255,255,0.45)"

    accent: str = "#4CC2FF"
    accent_hover: str = "#5BC9FF"
    on_accent: str = "#04304A"

    # entity-kind colors (distinct hues; shared by table + minimap)
    self_: str = "#33D9B2"
    player: str = "#4CC2FF"
    monster: str = "#FF6B6B"
    npc: str = "#B6BDC7"
    target: str = "#FFC24B"


@dataclass(frozen=True)
class Metrics:
    """One spacing scale + one control height; everything aligns to these."""

    gap_s: int = 6
    gap: int = 8
    gutter: int = 16            # standard spacing between groups
    pad_card: int = 16
    pad_page: int = 24

    ctl_h: int = 32             # ALL interactive controls share this height
    header_h: int = 56
    nav_h: int = 38
    sidebar_w: int = 208

    radius: int = 8             # cards
    radius_ctl: int = 6         # buttons / inputs

    fs_title: int = 20
    fs_brand: int = 15
    fs_body: int = 13
    fs_small: int = 12
    fs_caps: int = 11

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
        font-size: {m.fs_body}px;
        color: {c.text};
        outline: none;
    }}
    QWidget#root, QMainWindow {{ background: {c.bg}; }}

    /* sidebar */
    QWidget#sidebar {{ background: {c.sidebar}; }}
    QLabel#brand {{ font-size: {m.fs_brand}px; font-weight: 700; }}
    QLabel#brandAccent {{ font-size: {m.fs_brand}px; font-weight: 700; color: {c.accent}; }}
    QLabel#navHint {{ color: {c.faint}; font-size: {m.fs_small}px; }}
    QPushButton#nav {{
        text-align: left; padding: 0 12px; min-height: {m.nav_h}px; border: none;
        border-left: 3px solid transparent; border-radius: {m.radius_ctl}px;
        color: {c.muted}; background: transparent; font-weight: 600;
    }}
    QPushButton#nav:hover {{ background: {c.divider}; color: {c.text}; }}
    QPushButton#nav:checked {{
        background: {c.control}; color: {c.text}; border-left: 3px solid {c.accent};
    }}
    QPushButton#nav:disabled {{ color: {c.faint}; background: transparent; }}

    /* header */
    QWidget#header {{ background: {c.bg}; border-bottom: 1px solid {c.divider}; }}
    QLabel#pageTitle {{ font-size: {m.fs_title}px; font-weight: 700; }}
    QLabel#muted {{ color: {c.muted}; font-size: {m.fs_small}px; }}
    QLabel#status {{ color: {c.muted}; }}
    QLabel#mono {{ font-family: {m.font_mono}; color: {c.text}; }}
    QLabel#monoMuted {{ font-family: {m.font_mono}; color: {c.muted}; }}

    /* cards / panels */
    QFrame#card {{
        background: {c.card}; border: 1px solid {c.border}; border-radius: {m.radius}px;
    }}
    QLabel#cardTitle {{
        color: {c.muted}; font-weight: 700; font-size: {m.fs_caps}px; letter-spacing: 1px;
    }}

    /* table */
    QTableView {{
        background: transparent; border: none; gridline-color: transparent;
        selection-background-color: {c.divider}; selection-color: {c.text};
    }}
    QHeaderView::section {{
        background: transparent; color: {c.faint}; border: none;
        border-bottom: 1px solid {c.border}; padding: 6px 8px;
        font-weight: 700; font-size: {m.fs_small}px;
    }}
    QTableView::item {{ padding: 5px 8px; border: none; }}

    /* buttons (one style family; #toggle is the segmented variant) */
    QPushButton#toggle {{
        background: {c.control}; border: 1px solid {c.border}; border-radius: {m.radius_ctl}px;
        padding: 0 14px; color: {c.muted}; font-weight: 600;
    }}
    QPushButton#toggle:hover {{ background: {c.control_hover}; color: {c.text}; }}
    QPushButton#toggle:checked {{
        background: {c.accent}; border-color: {c.accent}; color: {c.on_accent};
    }}

    /* slider */
    QSlider {{ min-height: {m.ctl_h}px; }}
    QSlider::groove:horizontal {{ height: 4px; background: {c.control}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: {c.accent}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        background: {c.text}; width: 14px; height: 14px; margin: -6px 0; border-radius: 7px;
    }}
    QSlider::handle:horizontal:hover {{ background: {c.accent}; }}

    /* scrollbars */
    QSplitter::handle {{ background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {c.border}; border-radius: 5px; min-height: 28px; }}
    QScrollBar::handle:vertical:hover {{ background: {c.faint}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    """
