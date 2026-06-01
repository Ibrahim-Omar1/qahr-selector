"""ui/icons — render Segoe Fluent Icons glyphs to QIcons.

Windows 11 ships "Segoe Fluent Icons" (with "Segoe MDL2 Assets" as fallback);
both expose the same Private-Use codepoints used below. Rendering a glyph to a
pixmap lets a QPushButton show icon + text and collapse to icon-only.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

_ICON_FAMILY = "Segoe Fluent Icons"

# Segoe Fluent / MDL2 Assets codepoints (Private Use Area).
NAV_MENU = chr(0xE700)   # GlobalNavButton (hamburger)
RADAR = chr(0xE890)      # View (eye)
COMBAT = chr(0xE7FC)     # Game (controller)
MOVEMENT = chr(0xE816)   # MapDirections
SETTINGS = chr(0xE713)   # Settings (gear)


def glyph_icon(codepoint: str, color: str, px: int = 18) -> QIcon:
    """Render an icon-font glyph into a QIcon at size ``px``."""
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    font = QFont(_ICON_FAMILY)
    font.setPixelSize(px)
    p.setFont(font)
    p.setPen(QColor(color))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, codepoint)
    p.end()
    return QIcon(pm)
