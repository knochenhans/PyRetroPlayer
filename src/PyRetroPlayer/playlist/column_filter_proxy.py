from typing import Optional, Union

from PySide6.QtCore import (
    QMimeData,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtWidgets import QWidget


class ColumnFilterProxy(QSortFilterProxyModel):
    def __init__(self, visible_columns: set[int], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.set_visible_columns(visible_columns)

    def set_visible_columns(self, cols: set[int]):
        self._visible_columns = cols
        self.invalidateFilter()

    def filterAcceptsColumn(
        self,
        source_column: int,
        source_parent: Union[QModelIndex, QPersistentModelIndex],
    ) -> bool:
        return source_column in self._visible_columns

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        # Map proxy parent to source parent
        src_parent = self.mapToSource(parent)

        # Map proxy column to source column
        if column != -1:
            src_col = self.mapToSource(self.index(0, column)).column()
        else:
            src_col = -1

        return self.sourceModel().dropMimeData(data, action, row, src_col, src_parent)
