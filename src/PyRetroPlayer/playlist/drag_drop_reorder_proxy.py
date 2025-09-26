from typing import List, Optional, Sequence

from PySide6.QtCore import (
    QAbstractProxyModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    QAbstractItemModel,
    QMimeData,
)
from PySide6.QtWidgets import QWidget


class DragDropReorderProxy(QAbstractProxyModel):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._row_order: list[int] = []

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

        if not hasattr(self, "_current_drag_row"):
            return False

        self.beginResetModel()
        sel = self._row_order.pop(self._current_drag_row)
        self._row_order.insert(min(row, len(self._row_order)), sel)
        self.endResetModel()

        return True

    def mimeTypes(self) -> List[str]:
        return ["application/x-qabstractitemmodeldatalist"]

    def mimeData(self, indexes: Sequence[QModelIndex]) -> QMimeData:
        # Track the dragged row
        if indexes:
            self._current_drag_row = indexes[0].row()
        return super().mimeData(indexes)
