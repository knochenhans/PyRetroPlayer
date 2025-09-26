from typing import Any, Dict, List, Optional
import json

from icons import Icons  # type: ignore
from loguru import logger
from playlist.column_filter_proxy import ColumnFilterProxy  # type: ignore
from playlist.column_manager import ColumnManager  # type: ignore
from playlist.drag_drop_reorder_proxy import DragDropReorderProxy  # type: ignore
from playlist.playlist import Playlist  # type: ignore
from playlist.playlist_item_model import PlaylistItemModel  # type: ignore
from playlist.song_library import SongLibrary  # type: ignore
from PySide6.QtCore import (
    QModelIndex,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QBrush,
    QDropEvent,
    QIcon,
    QKeyEvent,
    QPainter,
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
from settings.settings import Settings  # type: ignore


class CustomItemViewStyle(QProxyStyle):
    def __init__(self, style: Optional[QStyle] = None):
        super().__init__(style)

    def drawPrimitive(
        self,
        element: QStyle.PrimitiveElement,
        option: QStyleOption,
        painter: QPainter,
        widget: Optional[QWidget] = None,
    ):
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

        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        self.setDragDropOverwriteMode(False)
        # self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

        # Apply custom style for the drop indicator
        self.setStyle(CustomItemViewStyle(self.style()))

        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.setRootIsDecorated(False)
        self.header().setMinimumSectionSize(20)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.doubleClicked.connect(self.on_item_double_clicked)

        self.source_model = PlaylistItemModel(0, len(self.default_columns_definitions))

        column_names = [
            col_def.get("name", "") for col_def in self.default_columns_definitions
        ]

        self.source_model.set_column_names(column_names)

        filtered_cols = self.column_manager.get_visible_column_indices()
        # filtered_cols = [2, 3]
        col_proxy = ColumnFilterProxy(set(filtered_cols))
        col_proxy.setSourceModel(self.source_model)

        reorder_proxy = DragDropReorderProxy()
        reorder_proxy.setSourceModel(col_proxy)
        reorder_proxy.rowsReordered.connect(playlist.set_song_order)

        self.setModel(reorder_proxy)

        self.update_playlist_data()
        # self.hide_invisible_columns()
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

    def keyPressEvent(self, event: QKeyEvent):
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

    # def setModel(self, model: Optional[QAbstractItemModel]) -> None:
    #     super().setModel(model)
    #     # Only assign if model is a ColumnFilterProxy
    #     if isinstance(model, ColumnFilterProxy):
    #         self.playlist_model = model

    def on_item_double_clicked(self, index: QModelIndex) -> None:
        self.item_double_clicked.emit(index.row())

    def update_playlist_data(self) -> None:
        songs = self.playlist.get_song_metadata(self.song_library)

        data: List[Dict[str, str]] = []
        for song in songs:
            row_data: Dict[str, str] = {}
            for column_def in self.default_columns_definitions:
                col_id = column_def.get("id", "")

                # if col_id == "playing":
                #     continue

                match col_id:
                    case "title":
                        row_data[col_id] = song.title
                    case "artist":
                        row_data[col_id] = song.artist
                    case "file_path":
                        row_data[col_id] = song.file_path
                    case "duration":
                        row_data[col_id] = str(song.duration)
                    case "backend_name":
                        row_data[col_id] = song.backend_name or ""
                    case _:
                        custom_metadata = song.custom_metadata or {}
                        row_data[col_id] = custom_metadata.get(col_id, "")

            data.append(row_data)

            logger.debug(f"Adding row data: {row_data}")

        self.model().removeRows(0, self.model().rowCount())
        for row_data in data:
            self.add_row(row_data)

    def add_row(self, row_data: Dict[str, Any]) -> None:
        tree_cols: List[QStandardItem] = []
        for column_def in self.default_columns_definitions:
            col_id = column_def.get("id", "")

            # if col_id == "playing":
            #     continue

            item = QStandardItem(row_data.get(col_id, ""))

            logger.debug(f"Adding item: {col_id} with value: {item.text()}")

            tree_cols.append(item)
        self.source_model.appendRow(tree_cols)

    def remove_row(self, row: int) -> None:
        self.source_model.removeRow(row)
        song_id = self.playlist.get_songs()[row]
        self.playlist.remove_song(song_id)

    def get_selected_rows(self) -> List[int]:
        return sorted(set(index.row() for index in self.selectedIndexes()))

    # def dragEnterEvent(self, event: QDragEnterEvent) -> None:
    #     if event.mimeData().hasUrls():
    #         event.acceptProposedAction()
    #     super().dragEnterEvent(event)

    # def dragMoveEvent(self, event: QDragMoveEvent) -> None:
    #     if event.mimeData().hasUrls():
    #         event.acceptProposedAction()
    #     super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = [url.toLocalFile() for url in urls]
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()
        super().dropEvent(event)

    def _set_play_status(self, row: int, enable: bool) -> None:
        column = self.source_model.itemFromIndex(self.model().index(row, 0))

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
            return self.source_model.itemFromIndex(index)
        return None

    def get_column_widths(self) -> List[int]:
        column_widths: List[int] = []
        for i in range(self.model().columnCount()):
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

    def load_playlist(self, file_path: str) -> Optional[Playlist]:
        try:
            with open(file_path, "r") as f:
                playlist_data = json.load(f)
                logger.info(f"Loaded playlist: {playlist_data['name']}")
                return Playlist(
                    id=playlist_data["id"],
                    name=playlist_data["name"],
                    song_ids=playlist_data["song_ids"],
                )
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            logger.error(f"Failed to load playlist from {file_path}: {e}")
            return None

    def save_playlist(self, playlist: Playlist, file_path: str) -> None:
        try:
            with open(file_path, "w") as f:
                json.dump(
                    {
                        "id": playlist.id,
                        "name": playlist.name,
                        "song_ids": playlist.get_songs(),
                    },
                    f,
                    indent=4,
                )
            logger.info(f"Playlist saved to {file_path}")
        except IOError as e:
            logger.error(f"Failed to save playlist to {file_path}: {e}")


    # def hide_invisible_columns(self) -> None:
    #     for i, column_id in enumerate(self.column_manager.columns):
    #         hidden = not self.column_manager.is_column_visible(column_id)
    #         self.setColumnHidden(i, hidden)
    #         logger.debug(f"{'Hiding' if hidden else 'Showing'} column: {column_id}")
