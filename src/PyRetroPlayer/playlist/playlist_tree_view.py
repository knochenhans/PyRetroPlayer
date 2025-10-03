from enum import Enum, auto
from typing import Any, Dict, List, Optional

from loguru import logger
from PySide6.QtCore import (
    QItemSelectionModel,
    QModelIndex,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QDragEnterEvent,
    QDropEvent,
    QIcon,
    QKeyEvent,
    QPainter,
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

from PyRetroPlayer.playlist.column_filter_proxy import ColumnFilterProxy
from PyRetroPlayer.playlist.column_manager import ColumnManager
from PyRetroPlayer.playlist.drag_drop_reorder_proxy import (
    DragDropReorderProxy,
)
from PyRetroPlayer.playlist.playlist import Playlist
from PyRetroPlayer.playlist.playlist_entry import PlaylistEntry
from PyRetroPlayer.playlist.playlist_item_model import PlaylistItemModel
from PyRetroPlayer.playlist.song import Song
from PyRetroPlayer.playlist.song_info_dialog import SongInfoDialog
from PyRetroPlayer.playlist.song_library import SongLibrary
from PyRetroPlayer.settings.settings import Settings


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
            and not option.rect.isNull()
        ):
            opt = QStyleOption(option)
            opt.rect.setLeft(0)
            if widget:
                opt.rect.setRight(widget.width())

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

    class PlayerState(Enum):
        STOPPED = auto()
        PLAYING = auto()
        PAUSED = auto()

    def __init__(
        self,
        settings: Settings,
        playlist: Playlist,
        column_manager: ColumnManager,
        default_columns_definitions: List[Dict[str, Any]],
        song_library: SongLibrary,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self.settings = settings
        self.playlist = playlist
        self.column_manager = column_manager
        self.default_columns_definitions = default_columns_definitions
        self.song_library = song_library

        self.previous_row = -1

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

        col_proxy = ColumnFilterProxy(set(filtered_cols))
        col_proxy.setSourceModel(self.source_model)

        reorder_proxy = DragDropReorderProxy()
        reorder_proxy.setSourceModel(col_proxy)
        reorder_proxy.rowsReordered.connect(playlist.set_song_order)

        self.setModel(reorder_proxy)

        selectionModel = QItemSelectionModel(self.model())
        selectionModel.SelectionFlag(
            QItemSelectionModel.SelectionFlag.SelectCurrent
            | QItemSelectionModel.SelectionFlag.Clear
        )
        self.setSelectionModel(selectionModel)

        self.get_playlist_data()
        self.set_column_widths(self.column_manager.get_column_widths())

        playlist.song_added = self.on_entry_added
        playlist.song_removed = self.on_entry_removed
        playlist.song_playing = self.set_currently_playing_entry

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            self.remove_selected_rows()
        else:
            super().keyPressEvent(event)

    def remove_selected_rows(self):
        selected_rows = self.get_selected_rows()
        for row in reversed(selected_rows):  # Reverse to avoid index shifting
            self.remove_row(row)

    def set_selected_item_played(self):
        index = self.currentIndex()
        if index.isValid():
            row = index.row()
            print(f"Playing item at row {row}")
            self.set_currently_playing_row(row)

    def on_item_double_clicked(self, index: QModelIndex) -> None:
        self.item_double_clicked.emit(index.row())

    def build_row_data(self, entry: PlaylistEntry) -> Dict[str, str]:
        song = self.song_library.get_song(entry.song_id)

        if not song:
            logger.error(f"Song with ID {entry.song_id} not found in library")
            return {}

        row_data: Dict[str, str] = {}
        for column_def in self.default_columns_definitions:
            col_id = column_def.get("id", "")
            match col_id:
                case "entry_id":
                    row_data[col_id] = entry.entry_id
                case "song_id":
                    row_data[col_id] = song.id
                case "title":
                    row_data[col_id] = song.title
                case "artist":
                    row_data[col_id] = song.artist
                case "file_name":
                    row_data[col_id] = (
                        song.file_path.split("/")[-1] if song.file_path else ""
                    )
                case "file_path":
                    row_data[col_id] = song.file_path
                case "duration":
                    if not song.duration:
                        row_data[col_id] = "0:00"
                        continue
                    seconds = int(song.duration // 1000)
                    minutes = seconds // 60
                    hours = minutes // 60
                    seconds = seconds % 60
                    minutes = minutes % 60
                    if hours > 0:
                        row_data[col_id] = f"{hours}:{minutes:02}:{seconds:02}"
                    else:
                        row_data[col_id] = f"{minutes}:{seconds:02}"
                case "available_backends":
                    row_data[col_id] = (
                        ", ".join(song.available_backends)
                        if song.available_backends
                        else ""
                    )
                case _:
                    custom_metadata = song.custom_metadata or {}
                    row_data[col_id] = custom_metadata.get(col_id, "")
        logger.debug(f"Loaded song data: {row_data} into playlist tree view")
        return row_data

    def get_playlist_data(self) -> None:
        playlist_entries = self.playlist.get_songs_metadata(self.song_library)

        data: List[Dict[str, str]] = []
        for playlist_entry in playlist_entries:
            row_data = self.build_row_data(playlist_entry)
            data.append(row_data)
            # logger.debug(f"Adding row data: {row_data}")

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

            # logger.debug(f"Adding item: {col_id} with value: {item.text()}")

            tree_cols.append(item)
        self.source_model.appendRow(tree_cols)

    def remove_row(self, row: int) -> None:
        self.source_model.removeRow(row)
        song_id = self.playlist.get_song_ids()[row]
        self.playlist.remove_song(song_id)

    def get_selected_rows(self) -> List[int]:
        return sorted(set(index.row() for index in self.selectedIndexes()))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = [url.toLocalFile() for url in urls]
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def _set_play_status(self, row: int, state: "PlaylistTreeView.PlayerState") -> None:
        item = self.source_model.item(
            row, self.column_manager.get_column_index("playing")
        )

        if item:
            if state == self.PlayerState.PLAYING:
                item.setIcon(QIcon.fromTheme("media-playback-start"))
            elif state == self.PlayerState.PAUSED:
                item.setIcon(QIcon.fromTheme("media-playback-pause"))
            else:  # STOPPED
                item.setIcon(QIcon())
            self.viewport().update()

    def set_currently_playing_row(self, row: int) -> None:
        if self.previous_row != -1:
            self._set_play_status(self.previous_row, self.PlayerState.STOPPED)
        self._set_play_status(row, self.PlayerState.PLAYING)
        self.previous_row = row

    def clear_currently_playing(self) -> None:
        if self.previous_row != -1:
            self._set_play_status(self.previous_row, self.PlayerState.STOPPED)
            self.previous_row = -1

    def pause_currently_playing(self) -> None:
        if self.previous_row != -1:
            self._set_play_status(self.previous_row, self.PlayerState.PAUSED)

    def start_currently_playing(self) -> None:
        if self.previous_row != -1:
            self._set_play_status(self.previous_row, self.PlayerState.PLAYING)

    def set_currently_playing_entry(self, entry: Optional[PlaylistEntry]) -> None:
        if entry is None:
            return

        for row in range(self.source_model.rowCount()):
            item = self.source_model.item(
                row, self.column_manager.get_column_index("entry_id")
            )
            if item and item.text() == entry.entry_id:
                self.set_currently_playing_row(row)
                self.setCurrentIndex(self.model().index(row, 0))
                return
        logger.warning(f"Entry ID {entry.entry_id} not found in playlist view")

    def get_current_item(self) -> Optional[QStandardItem]:
        index = self.currentIndex()
        if index.isValid():
            return self.source_model.itemFromIndex(index)
        return None

    def get_current_index(self) -> Optional[int]:
        index = self.currentIndex()
        if index.isValid():
            return index.row()
        return None

    def get_current_entry(self) -> Optional[PlaylistEntry]:
        current_index = self.get_current_index()
        if current_index is not None and 0 <= current_index < len(
            self.playlist.entries
        ):
            return self.playlist.entries[current_index]
        return None

    def get_current_song_id(self) -> Optional[str]:
        entry = self.get_current_entry()
        if entry:
            return entry.song_id
        return None

    def get_current_song(self) -> Optional[Song]:
        song_id = self.get_current_song_id()
        if song_id:
            return self.song_library.get_song(song_id)
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

    def on_entry_added(self, entry: PlaylistEntry) -> None:
        song = self.song_library.get_song(entry.song_id)
        if song:
            row_data = self.build_row_data(entry)
            self.add_row(row_data)
            logger.info(f"Song added to playlist view: {song.title} by {song.artist}")
        else:
            logger.warning(f"Song ID {entry.song_id} not found in library; cannot add.")

    def on_entry_removed(self, entry: PlaylistEntry) -> None:
        song = self.song_library.get_song(entry.song_id)
        if song:
            try:
                row = self.playlist.get_song_ids().index(song.id)
                self.remove_row(row)
                logger.info(
                    f"Song removed from playlist view: {song.title} by {song.artist}"
                )
            except ValueError:
                logger.warning(
                    f"Song ID {entry.song_id} not found in playlist; cannot remove row."
                )
        else:
            logger.warning(
                f"Song ID {entry.song_id} not found in library; cannot remove."
            )

    def on_song_info_dialog(self) -> None:
        current_song = self.get_current_song()
        if current_song:
            dialog = SongInfoDialog(current_song, self)
            dialog.exec()
        if current_song:
            dialog = SongInfoDialog(current_song, self)
            dialog.exec()
