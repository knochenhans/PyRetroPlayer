from typing import List, Optional, Union

from PySide6.QtCore import QMimeData, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QWidget


class PlaylistModel(QStandardItemModel):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(0, 0, parent)

    def flags(self, index: Union[QModelIndex, QPersistentModelIndex]) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.ItemIsDropEnabled
        else:
            return (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsDragEnabled
            )

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: Union[QModelIndex, QPersistentModelIndex],
    ) -> bool:
        if action == Qt.DropAction.IgnoreAction:
            return False

        if action == Qt.DropAction.MoveAction:
            if action == Qt.DropAction.IgnoreAction:
                return False

        if action == Qt.DropAction.MoveAction:
            # Prevent shifting columns
            return super().dropMimeData(data, Qt.DropAction.CopyAction, row, 0, parent)

        return False

    def supportedDragActions(self) -> Qt.DropAction:
        return Qt.DropAction.MoveAction

    def supportedDropActions(self) -> Qt.DropAction:
        return Qt.DropAction.MoveAction

    def mimeTypes(self) -> List[str]:
        return ["application/x-qstandarditemmodeldatalist"]

    def set_column_names(self, column_names: List[str]) -> None:
        self.setHorizontalHeaderLabels(column_names)
