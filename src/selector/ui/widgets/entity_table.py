"""ui/widgets/entity_table — table model + view for the radar entity list.

A small ``QAbstractTableModel`` over ``list[Entity]``; the kind cell is tinted
with the shared kind color. Updates in place when the row count is unchanged
(so scroll/selection survive the ~7 Hz refresh) and only resets on a count
change.
"""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableView, QWidget

from selector.core.models import Entity
from selector.ui.theme import kind_color

_HEADERS = ("Kind", "Name", "Tile", "Dist", "PK")
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
                f"{e.x}, {e.y}",
                str(e.dist),
                e.pk_name or "—",
            )[col]
        if role == Qt.ItemDataRole.ForegroundRole and col == 0:
            return QColor(kind_color(e.kind))
        if role == Qt.ItemDataRole.TextAlignmentRole and col in (2, 3):
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None


class EntityTable(QTableView):
    """A QTableView pre-configured for the radar (no edit, row select, stretch)."""

    def __init__(self, model: EntityTableModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModel(model)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.horizontalHeader().setHighlightSections(False)
        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name stretches
        for col in (0, 2, 3, 4):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
