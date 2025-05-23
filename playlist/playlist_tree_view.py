from typing import Any, Dict, List, Optional

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QBrush,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QIcon,
    QPalette,
    QStandardItem,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QProxyStyle,
    QStyle,
    QStyleOption,
    QTreeView,
    QWidget,
)

from icons import Icons
from playlist.column_manager import ColumnManager
from playlist.playlist import Playlist
from playlist.playlist_model import PlaylistModel
from playlist.song_library import SongLibrary
from settings.settings import Settings

# from tree_view_columns import tree_view_columns_dict


class CustomItemViewStyle(QProxyStyle):
    def __init__(self, style=None):
        super().__init__(style)

    def drawPrimitive(self, element, option, painter, widget=None):
        if (
            element == QStyle.PrimitiveElement.PE_IndicatorItemViewItemDrop
            and not option.rect.isNull()  # type: ignore
        ):
            opt = QStyleOption(option)
            opt.rect.setLeft(0)  # type: ignore
            if widget:
                opt.rect.setRight(widget.width())  # type: ignore

            pen = painter.pen()
            pen.setWidth(3)
            painter.setPen(pen)

            super().drawPrimitive(element, opt, painter, widget)
            return
        super().drawPrimitive(element, option, painter, widget)


class PlaylistTreeView(QTreeView):
    item_double_clicked = Signal(int)
    files_dropped = Signal(list)
    rows_moved = Signal(list)

    def __init__(
        self,
        icons: Icons,
        settings: Settings,
        playlist: Playlist,
        column_manager: ColumnManager,
        default_columns_definitions: List[Dict[str, Any]],
        song_library: SongLibrary,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self.icons = icons
        self.settings = settings
        self.playlist = playlist
        self.column_manager = column_manager
        self.default_columns_definitions = default_columns_definitions
        self.song_library = song_library

        # Enable drag-and-drop reordering
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

        # Apply custom style for the drop indicator
        self.setStyle(CustomItemViewStyle(self.style()))

        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.setRootIsDecorated(False)
        self.header().setMinimumSectionSize(20)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.doubleClicked.connect(self.on_item_double_clicked)

        # Initialize the model and set the playlist data
        model = PlaylistModel(self)
        model.set_column_names(self.column_manager.get_column_names())
        self.setModel(model)
        self.model().rowsMoved.connect(self.on_rows_moved)

        self.set_playlist_data(self.get_playlist_data())
        self.remove_invisible_columns()
        self.set_column_widths(self.column_manager.get_column_widths())

        self.add_context_menu_actions()

    def add_context_menu_actions(self):
        # Action to remove selected rows
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.remove_selected_rows)
        self.addAction(remove_action)

        # Action to play the selected item
        play_action = QAction("Play", self)
        play_action.triggered.connect(self.play_selected_item)
        self.addAction(play_action)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.remove_selected_rows()
        else:
            super().keyPressEvent(event)

    def remove_selected_rows(self):
        selected_rows = self.get_selected_rows()
        for row in reversed(selected_rows):  # Reverse to avoid index shifting
            self.remove_row(row)

    def play_selected_item(self):
        index = self.currentIndex()
        if index.isValid():
            row = index.row()
            print(f"Playing item at row {row}")
            self.set_currently_playing_row(row)

    def setModel(self, model: PlaylistModel) -> None:
        super().setModel(model)
        self.playlist_model = model

    def on_item_double_clicked(self, index: QModelIndex) -> None:
        self.item_double_clicked.emit(index.row())

    def set_playlist_data(self, data: List[Dict[str, Any]]) -> None:
        self.playlist_model.removeRows(0, self.playlist_model.rowCount())
        for row_data in data:
            self.add_row(row_data)

    def add_row(self, row_data: Dict[str, Any]) -> None:
        tree_cols = []
        for column_def in self.default_columns_definitions:
            col_id = column_def.get("id", "")
            item = QStandardItem(row_data.get(col_id, ""))
            tree_cols.append(item)
        self.playlist_model.appendRow(tree_cols)

    def remove_row(self, row: int) -> None:
        self.playlist_model.removeRow(row)
        song_id = self.playlist.get_songs()[row]
        self.playlist.remove_song(song_id)

    def get_selected_rows(self) -> List[int]:
        return sorted(set(index.row() for index in self.selectedIndexes()))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = [url.toLocalFile() for url in urls]
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()
        super().dropEvent(event)

    def _set_play_status(self, row: int, enable: bool) -> None:
        column = self.playlist_model.itemFromIndex(self.model().index(row, 0))

        if column:
            color = column.foreground().color()

            if enable:
                column.setData(
                    self.icons.pixmap_icons["play"], Qt.ItemDataRole.DecorationRole
                )
                color.setRgb(255 - color.red(), 255 - color.green(), 255 - color.blue())
            else:
                column.setData(QIcon(), Qt.ItemDataRole.DecorationRole)

                default_color = self.palette().color(QPalette.ColorRole.Text)
                color.setRgb(
                    default_color.red(), default_color.green(), default_color.blue()
                )

            column.setForeground(QBrush(color))

    def set_currently_playing_row(self, row: int) -> None:
        self._set_play_status(self.previous_row, False)
        self._set_play_status(row, True)
        self.previous_row = row

    def get_current_item(self) -> Optional[QStandardItem]:
        index = self.currentIndex()
        if index.isValid():
            return self.playlist_model.itemFromIndex(index)
        return None

    def get_column_widths(self) -> List[int]:
        column_widths = []
        for i in range(self.playlist_model.columnCount()):
            column_widths.append(self.columnWidth(i))
        return column_widths

    def set_column_widths(self, widths: List[int]) -> None:
        for i, width in enumerate(widths):
            self.setColumnWidth(i, width)

    def update_column_width(self) -> None:
        column_index = 0
        for column_id in self.column_manager.get_column_ids():
            if self.column_manager.is_column_visible(column_id):
                current_width = self.columnWidth(column_index)
                self.column_manager.set_column_width(column_id, current_width)
                column_index += 1

    def on_rows_moved(
        self,
        parent: QModelIndex,
        start: int,
        end: int,
        destination: QModelIndex,
        row: int,
    ) -> None:

        # Emit the new order of rows
        new_order = [
            self.model().index(i, 0).row() for i in range(self.model().rowCount())
        ]
        self.rows_moved.emit(new_order)

    def remove_invisible_columns(self) -> None:
        model = self.model()
        i = 0
        for column_id in self.column_manager.columns:
            if not self.column_manager.is_column_visible(column_id):
                model.removeColumn(i)
            else:
                i += 1

    def get_playlist_data(self) -> List[Dict[str, Any]]:
        songs = self.playlist.get_song_metadata(self.song_library)

        data = []
        for song in songs:
            row_data = {}
            for column_def in self.default_columns_definitions:
                col_id = column_def.get("id", "")
                if col_id == "title":
                    row_data[col_id] = song.title
                elif col_id == "artist":
                    row_data[col_id] = song.artist
                elif col_id == "file_path":
                    row_data[col_id] = song.file_path
            data.append(row_data)
        return data
