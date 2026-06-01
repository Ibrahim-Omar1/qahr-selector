"""ui/widgets/entity_table — table model + view for the radar entity list.

A small ``QAbstractTableModel`` over ``list[Entity]``; the kind cell is tinted
with the shared kind color. Updates in place when the row count is unchanged
(so scroll/selection survive the ~7 Hz refresh) and only resets on a count
change.
"""
from __future__ import annotations

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    QRectF,
    QSize,
    Qt,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QWidget,
)

from selector.core.models import Entity
from selector.ui.theme import COLORS, METRICS, kind_color

_HEADERS = ("Kind", "Name", "UID", "Tile", "Dist", "PK")
_Index = QModelIndex | QPersistentModelIndex  # Qt's index argument type


class EntityTableModel(QAbstractTableModel):
    """Read-only table of nearby entities."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list[Entity] = []

    def set_entities(self, entities: list[Entity]) -> None:
        if len(entities) != len(self._rows):
            self.beginResetModel()
            self._rows = list(entities)
            self.endResetModel()
            return
        self._rows = list(entities)
        if self._rows:
            top = self.index(0, 0)
            bottom = self.index(len(self._rows) - 1, len(_HEADERS) - 1)
            self.dataChanged.emit(top, bottom)

    # --- Qt model API ---------------------------------------------------------
    def rowCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802,B008
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: N802,B008
        return 0 if parent.isValid() else len(_HEADERS)

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> object:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return _HEADERS[section]
        return None

    def data(self, index: _Index, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid():
            return None
        e = self._rows[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return (
                e.kind.value,
                e.name or "—",
                str(e.uid),
                f"{e.x}, {e.y}",
                str(e.dist),
                e.pk_name or "—",
            )[col]
        if role == Qt.ItemDataRole.ForegroundRole and col == 0:
            return QColor(kind_color(e.kind))
        if role == Qt.ItemDataRole.TextAlignmentRole and col in (2, 3, 4):
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None


class KindChipDelegate(QStyledItemDelegate):
    """Paints the Kind cell as a rounded color chip (tinted bg + colored text)."""

    _CHIP_H = 20
    _PAD = 9

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: _Index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = option.rect
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        # row background (match the rest of the row)
        if selected:
            painter.fillRect(rect, QColor(139, 92, 246, 41))      # accent_soft
        elif index.row() % 2:
            painter.fillRect(rect, QColor(COLORS.card_alt))
        # chip
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        fg = index.data(Qt.ItemDataRole.ForegroundRole)
        color = fg if isinstance(fg, QColor) else QColor(COLORS.npc)
        tw = option.fontMetrics.horizontalAdvance(text)
        chip = QRectF(rect.left() + 8, rect.center().y() - self._CHIP_H / 2 + 1,
                      tw + self._PAD * 2, self._CHIP_H)
        bg = QColor(color)
        bg.setAlpha(36)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(chip, self._CHIP_H / 2, self._CHIP_H / 2)
        painter.setPen(color)
        painter.drawText(chip, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: _Index) -> QSize:
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        tw = option.fontMetrics.horizontalAdvance(text)
        return QSize(tw + self._PAD * 2 + 16, METRICS.row_h)


class EntityTable(QTableView):
    """A QTableView pre-configured for the radar (no edit, row select, chips)."""

    def __init__(self, model: EntityTableModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModel(model)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(METRICS.row_h)
        self.setShowGrid(False)
        self.horizontalHeader().setHighlightSections(False)
        self.setItemDelegateForColumn(0, KindChipDelegate(self))
        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name stretches
        for col in (0, 2, 3, 4, 5):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
