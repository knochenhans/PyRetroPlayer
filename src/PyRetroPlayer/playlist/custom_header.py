from typing import Any, Dict, List, Optional

from PySide6.QtGui import (
    QContextMenuEvent,
    Qt,
)
from PySide6.QtWidgets import (
    QHeaderView,
    QMenu,
    QWidget,
)

from PyRetroPlayer.playlist.column_manager import ColumnManager


class CustomHeader(QHeaderView):
    def __init__(
        self,
        default_columns_definitions: List[Dict[str, Any]],
        column_manager: ColumnManager,
        parent: Optional[QWidget] = None,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
    ):
        super().__init__(orientation, parent)
        self.default_columns_definitions = default_columns_definitions
        self.column_manager = column_manager

        self.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

    def contextMenuEvent(self, arg__1: QContextMenuEvent) -> None:
        menu = QMenu(self)
        menu.addSeparator()

        for column_def in self.default_columns_definitions:
            col_id: str = column_def.get("id", "")
            col_name: str = column_def.get("name", "")

            action = menu.addAction(col_name)
            action.setCheckable(True)
            action.setChecked(self.column_manager.is_column_visible(col_id))

            def _on_action_toggled(checked: bool, col_id: str = col_id) -> None:
                self.on_column_visibility_toggled(col_id, checked)

            action.toggled.connect(_on_action_toggled)

        global_pos = self.mapToGlobal(arg__1.pos())
        menu.exec(global_pos)

    def on_column_visibility_toggled(self, column_id: str, visible: bool) -> None:
        self.column_manager.set_column_visibility(column_id, visible)
