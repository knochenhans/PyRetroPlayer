from typing import List

from PySide6.QtCore import (
    QMimeData,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
)
from PySide6.QtGui import QStandardItem, QStandardItemModel


class PlaylistModel(QStandardItemModel):
    def __init__(self, row_count: int, length: int = 0) -> None:
        super().__init__(row_count, length)

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        default_flags = super().flags(index)
        if not index.isValid():
            return Qt.ItemFlag.ItemIsDropEnabled | default_flags
        return (
            Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsDragEnabled
            | Qt.ItemFlag.ItemIsDropEnabled
        )

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        # Only allow drops at the top level (no parent)
        if parent.isValid():
            return False
        return super().dropMimeData(data, action, row, 0, parent)

    #     if action == Qt.DropAction.IgnoreAction:
    #         return False
    #     if not data.hasFormat("application/x-qstandarditemmodeldatalist"):
    #         return False

    #     if row == -1:
    #         row = self.rowCount()

    #     # Decode into a temp model
    #     temp_model = QStandardItemModel()
    #     temp_model.dropMimeData(data, Qt.DropAction.CopyAction, 0, 0, QModelIndex())

    #     # Collect rows
    #     copied_rows: List[List[QStandardItem]] = []
    #     for r in range(temp_model.rowCount()):
    #         items: List[QStandardItem] = []
    #         for c in range(temp_model.columnCount()):
    #             src_item = temp_model.item(r, c)
    #             if src_item:
    #                 item = src_item.clone()  # important: clone to avoid shared pointers
    #             else:
    #                 item = QStandardItem()
    #             items.append(item)
    #         copied_rows.append(items)

    #     # Insert at target
    #     for i, items in enumerate(copied_rows):
    #         self.insertRow(row + i, items)

    #     return True

    def mimeTypes(self) -> List[str]:
        return ["application/x-qstandarditemmodeldatalist"]

    def set_column_names(self, column_names: List[str]) -> None:
        self.setHorizontalHeaderLabels(column_names)
