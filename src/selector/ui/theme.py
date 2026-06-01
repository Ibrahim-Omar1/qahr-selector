"""ui/theme — the design system (tokens + global stylesheet).

A **Windows 11 / Fluent dark** system with a violet accent and a little
personality (gradient active-nav, accent-tinted hover/selection). One spacing
scale + one control height so everything aligns. Pure data + a QSS builder.
"""
from __future__ import annotations

from dataclasses import dataclass

from selector.core.models import EntityKind, Relation


@dataclass(frozen=True)
class Palette:
    """Color tokens (hex / rgba() strings, QSS-ready). 3 surface steps."""

    bg: str = "#1A1A1B"          # window base
    sidebar: str = "#202021"     # nav pane
    card: str = "#242425"        # panels
    card_alt: str = "#2A2A2C"    # alternating row / subtle raise
    control: str = "#2D2D2F"     # buttons / inputs
    control_hover: str = "#37373A"

    border: str = "rgba(255,255,255,0.08)"
    divider: str = "rgba(255,255,255,0.06)"

    text: str = "#F2F2F3"
    muted: str = "rgba(255,255,255,0.70)"
    faint: str = "rgba(255,255,255,0.42)"
    icon: str = "#C7C9D1"        # nav glyph color (needs a solid hex)

    accent: str = "#8B5CF6"      # violet
    accent_hover: str = "#9E78FF"
    accent_soft: str = "rgba(139,92,246,0.16)"     # tints (hover/selection)
    accent_soft2: str = "rgba(139,92,246,0.24)"
    on_accent: str = "#FFFFFF"

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
    gutter: int = 16
    pad_card: int = 18
    pad_page: int = 24

    ctl_h: int = 32
    header_h: int = 56
    nav_h: int = 40
    row_h: int = 34
    sidebar_w: int = 212
    sidebar_w_collapsed: int = 56

    radius: int = 8
    radius_ctl: int = 6

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


# Relationship colors (user spec): ally green, same guild yellow, enemy red.
_REL_COLOR: dict[Relation, str] = {
    Relation.SELF: COLORS.accent,
    Relation.GUILDMATE: "#FFD93D",   # yellow
    Relation.ALLY: "#3DDC84",        # green
    Relation.ENEMY: "#FF5C5C",       # red
}


def relation_color(rel: Relation) -> str | None:
    """Hex color for a relationship, or None for NEUTRAL (fall back to kind)."""
    return _REL_COLOR.get(rel)


def qss() -> str:
    """Global Qt stylesheet built from the tokens (Fluent dark, violet accent)."""
    c, m = COLORS, METRICS
    return f"""
    * {{
        font-family: {m.font_ui};
        font-size: {m.fs_body}px;
        color: {c.text};
        outline: none;
    }}
    QWidget#root, QMainWindow {{ background: {c.bg}; }}
    QToolTip {{
        background: {c.control}; color: {c.text}; border: 1px solid {c.border};
        padding: 4px 8px; border-radius: {m.radius_ctl}px;
    }}

    /* sidebar */
    QWidget#sidebar {{ background: {c.sidebar}; }}
    QLabel#brand {{ font-size: {m.fs_brand}px; font-weight: 700; }}
    QLabel#brandAccent {{ font-size: {m.fs_brand}px; font-weight: 800; color: {c.accent}; }}
    QLabel#navHint {{ color: {c.faint}; font-size: {m.fs_small}px; }}
    QPushButton#hamburger {{
        border: none; background: transparent; border-radius: {m.radius_ctl}px;
        min-height: {m.ctl_h}px; min-width: {m.ctl_h}px;
    }}
    QPushButton#hamburger:hover {{ background: {c.divider}; }}
    QPushButton#nav {{
        text-align: left; padding: 0 10px; min-height: {m.nav_h}px; border: none;
        border-left: 3px solid transparent; border-top-right-radius: {m.radius_ctl}px;
        border-bottom-right-radius: {m.radius_ctl}px;
        color: {c.muted}; background: transparent; font-weight: 600;
    }}
    QPushButton#nav:hover {{ background: {c.divider}; color: {c.text}; }}
    QPushButton#nav:checked {{
        color: {c.text}; border-left: 3px solid {c.accent};
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c.accent_soft2}, stop:1 {c.accent_soft});
    }}
    QPushButton#nav:disabled {{ color: {c.faint}; background: transparent; }}
    QPushButton#nav[collapsed="true"] {{ text-align: center; padding: 0; }}

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
        color: {c.faint}; font-weight: 700; font-size: {m.fs_caps}px; letter-spacing: 1.5px;
    }}

    /* table */
    QTableView {{
        background: transparent; border: none; gridline-color: transparent;
        alternate-background-color: {c.card_alt};
        selection-background-color: {c.accent_soft}; selection-color: {c.text};
    }}
    QHeaderView::section {{
        background: transparent; color: {c.faint}; border: none;
        border-bottom: 1px solid {c.border}; padding: 8px;
        font-weight: 700; font-size: {m.fs_small}px;
    }}
    QTableView::item {{ padding: 0 8px; border: none; }}

    /* buttons (one family; #toggle is the segmented variant) */
    QPushButton#toggle {{
        background: {c.control}; border: 1px solid {c.border}; border-radius: {m.radius_ctl}px;
        padding: 0 14px; color: {c.muted}; font-weight: 700;
    }}
    QPushButton#toggle:hover {{ background: {c.control_hover}; color: {c.text}; }}
    QPushButton#toggle:checked {{
        background: {c.accent}; border-color: {c.accent}; color: {c.on_accent};
    }}
    QPushButton#toggle:checked:hover {{ background: {c.accent_hover}; }}

    /* slider */
    QSlider {{ min-height: {m.ctl_h}px; }}
    QSlider::groove:horizontal {{ height: 4px; background: {c.control}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: {c.accent}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        background: {c.text}; width: 14px; height: 14px; margin: -6px 0; border-radius: 7px;
    }}
    QSlider::handle:horizontal:hover {{ background: {c.accent_hover}; }}

    /* scrollbars */
    QSplitter::handle {{ background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {c.border}; border-radius: 5px; min-height: 28px; }}
    QScrollBar::handle:vertical:hover {{ background: {c.faint}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    """
