from typing import List, Optional, Sequence

from PySide6.QtCore import (
    QAbstractItemModel,
    QAbstractProxyModel,
    QMimeData,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
)
from PySide6.QtWidgets import QWidget


class DragDropReorderProxy(QAbstractProxyModel):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._row_order: list[int] = []
        self._current_drag_rows: List[int] = []

    def setSourceModel(self, sourceModel: QAbstractItemModel) -> None:
        super().setSourceModel(sourceModel)
        # Connect signals so we update when the source changes
        sourceModel.modelReset.connect(self._reset_mapping)
        sourceModel.rowsInserted.connect(self._reset_mapping)
        sourceModel.rowsRemoved.connect(self._reset_mapping)
        self._reset_mapping()

    def _reset_mapping(self):
        # if self.sourceModel() is None:
        #     return
        self.beginResetModel()
        self._row_order = list(range(self.sourceModel().rowCount()))
        self.endResetModel()

    # Required abstract methods
    def rowCount(
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        # if parent.isValid() or self.sourceModel() is None:
        #     return 0
        return len(self._row_order)

    def columnCount(
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        # if self.sourceModel() is None:
        #     return 0
        return self.sourceModel().columnCount(parent)

    def index(
        self,
        row: int,
        column: int,
        parent: QModelIndex | QPersistentModelIndex = QModelIndex(),
    ) -> QModelIndex:
        if parent.isValid():
            return QModelIndex()
        if 0 <= row < self.rowCount() and 0 <= column < self.columnCount():
            return self.createIndex(row, column)
        return QModelIndex()

    def parent(self, index: QModelIndex | QPersistentModelIndex) -> QModelIndex:
        return QModelIndex()

    # Mapping
    def mapToSource(
        self, proxyIndex: QModelIndex | QPersistentModelIndex
    ) -> QModelIndex:
        if not proxyIndex.isValid():
            return QModelIndex()
        src_row = self._row_order[proxyIndex.row()]
        return self.sourceModel().index(src_row, proxyIndex.column())

    def mapFromSource(
        self, sourceIndex: QModelIndex | QPersistentModelIndex
    ) -> QModelIndex:
        if not sourceIndex.isValid():
            return QModelIndex()
        try:
            row = self._row_order.index(sourceIndex.row())
        except ValueError:
            return QModelIndex()
        return self.index(row, sourceIndex.column())

    # Drag/drop handling
    def supportedDropActions(self) -> Qt.DropAction:
        return Qt.DropAction.MoveAction

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        default = (
            Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsDragEnabled
        )
        if not index.isValid():
            return Qt.ItemFlag.ItemIsDropEnabled
        return default | Qt.ItemFlag.ItemIsDropEnabled

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        if action != Qt.DropAction.MoveAction:
            return False

        if row == -1 and parent.isValid():
            row = parent.row()
        elif row == -1:
            row = self.rowCount()

        # nothing to move
        if not getattr(self, "_current_drag_rows", None):
            return False

        # clamp row
        row = max(0, min(row, self.rowCount()))

        self.beginResetModel()

        # drag_rows in ascending order (proxy indices)
        drag_rows = sorted(self._current_drag_rows)

        # capture the values (source row ids) in original order
        moved = [self._row_order[r] for r in drag_rows]

        # remove from _row_order by popping descending indices to avoid shifts
        for r in sorted(drag_rows, reverse=True):
            self._row_order.pop(r)

        # if any removed rows were before the drop index, shift the drop index left
        num_before = sum(1 for r in drag_rows if r < row)
        row -= num_before
        row = max(0, min(row, len(self._row_order)))  # clamp again after adjustment

        # insert moved values preserving their original order
        for i, val in enumerate(moved):
            self._row_order.insert(row + i, val)

        self.endResetModel()

        # clear selection memory
        self._current_drag_rows = []
        return True

    # def mimeTypes(self) -> List[str]:
    #     return ["application/x-qabstractitemmodeldatalist"]

    def mimeData(self, indexes: Sequence[QModelIndex]) -> QMimeData:
        # Collect unique rows from selection (ascending order)
        if indexes:
            rows = sorted(set(idx.row() for idx in indexes))
            self._current_drag_rows = rows
        else:
            self._current_drag_rows = []
        return super().mimeData(indexes)
