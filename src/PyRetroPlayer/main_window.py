import json
import os
import sys
from typing import Any, Dict, List, Optional

from appdirs import user_config_dir, user_data_dir  # type: ignore
from importlib_resources import files
from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
)

from icons import Icons  # type: ignore
from loaders.fake_loader import FakeLoader  # type: ignore
from loaders.file_fetcher import FileFetcher  # type: ignore
from playlist.column_manager import ColumnManager  # type: ignore
from playlist.playlist import Playlist  # type: ignore
from playlist.playlist_manager import PlaylistManager  # type: ignore
from playlist.playlist_tab_widget import PlaylistTabWidget  # type: ignore
from playlist.playlist_tree_view import PlaylistTreeView  # type: ignore
from playlist.song import Song  # type: ignore
from playlist.song_library import SongLibrary  # type: ignore
from settings.settings import Settings  # type: ignore


class MainWindow(QMainWindow):
    progress_bar_value_changed = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        self.application_name: str = "PyRetroPlayer"
        self.application_version: str = "0.1.0"

        self.setWindowTitle(f"{self.application_name} v{self.application_version}")

        from ui_manager import UIManager  # type: ignore

        self.ui_manager = UIManager(self)

        config_dir = os.path.join(user_config_dir(), self.application_name)  # type: ignore
        os.makedirs(config_dir, exist_ok=True)

        data_dir = os.path.join(user_data_dir(), self.application_name)  # type: ignore
        os.makedirs(data_dir, exist_ok=True)

        self.playlist_configuration: Settings = Settings(
            "playlist_configuration", config_dir, self.application_name
        )
        self.playlist_configuration.ensure_default_config()
        self.playlist_configuration.load()

        self.playlist_manager = PlaylistManager(self.application_name)

        self.tab_widget: PlaylistTabWidget = PlaylistTabWidget(
            self, self.playlist_manager
        )
        self.tab_widget.tab_added.connect(self.create_new_playlist)
        self.tab_widget.tab_deleted.connect(self.on_delete_playlist)
        self.ui_manager.add_widget(self.tab_widget)

        self.ui_manager.create_menu_bar()

        default_columns_definitions = (
            files("data").joinpath("default_columns_configuration.json").read_text()
        )

        self.column_default_definitions: List[Dict[str, Any]] = json.loads(
            default_columns_definitions
        )

        self.column_managers: dict[str, ColumnManager] = {}

        self.song_library = SongLibrary(os.path.join(data_dir, "song_library.db"))

        # Load playlists and add tabs
        self.playlist_manager.load_playlists()
        for playlist in self.playlist_manager.playlists:
            self.add_playlist(playlist, self.load_or_create_column_manager(playlist))

        # Example songs
        # example_songs = [
        #     Song(title="song1.mp3", file_path="path/to/song1.mp3", artist="Artist 1"),
        #     Song(title="song2.mp3", file_path="path/to/song2.mp3", artist="Artist 2"),
        # ]
        # for song in example_songs:
        #     self.song_library.add_song(song)

        # playlist = Playlist(
        #     name="Example Playlist",
        # )

        # for song in self.song_library.get_all_songs():
        #     playlist.add_song(song.id)

        # column_manager = self.load_or_create_column_manager(playlist)
        # self.add_playlist(playlist, column_manager)

        # Create a new playlist if none exist
        if not self.playlist_manager.playlists:
            self.create_new_playlist()

    def create_new_playlist(self) -> None:
        playlist = Playlist(name="New Playlist")
        self.playlist_manager.add_playlist(playlist)
        self.add_playlist_with_manager(playlist)

    def on_delete_playlist(self) -> None:
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            self.tab_widget.on_tab_close(current_index)

    def import_playlist(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Playlist", "", "JSON Files (*.json)"
        )
        if file_path:
            playlist = self.playlist_manager.load_playlist(file_path)
            if playlist:
                self.add_playlist_with_manager(playlist)
                logger.info(f"Imported playlist: {playlist.name}")
                self.playlist_manager.add_playlist(playlist)
            else:
                logger.error("Failed to import playlist.")

    def export_playlist(self) -> None:
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            playlist = self.playlist_manager.playlists[current_index]
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Playlist", "", "JSON Files (*.json)"
            )
            if file_path:
                self.playlist_manager.save_playlist(playlist, file_path)
                logger.info(f"Exported playlist: {playlist.name}")

    def closeEvent(self, event: QCloseEvent) -> None:
        self.playlist_manager.save_playlists()
        self.tab_widget.update_tab_column_widths()
        self.save_column_managers()
        event.accept()

    def save_column_managers(self) -> None:
        columns_dir = os.path.join(self.playlist_manager.playlists_path, "columns")
        os.makedirs(columns_dir, exist_ok=True)

        for playlist_id, column_manager in self.column_managers.items():
            config_path = os.path.join(columns_dir, f"{playlist_id}.json")
            column_manager.save_to_json(config_path)

    def add_playlist(self, playlist: Playlist, column_manager: ColumnManager) -> None:
        icons = Icons(self.playlist_configuration, self.style())
        playlist_view = PlaylistTreeView(
            icons,
            self.playlist_configuration,
            playlist,
            column_manager,
            self.column_default_definitions,
            self.song_library,
            self,
        )

        playlist.name = playlist.name or ""
        self.tab_widget.addTab(playlist_view, playlist.name)
        self.column_managers[playlist.id] = column_manager

    def load_or_create_column_manager(self, playlist: Playlist) -> ColumnManager:
        config_path = os.path.join(
            self.playlist_manager.playlists_path,
            "columns",
            f"{playlist.id}.json",
        )
        if os.path.exists(config_path):
            return ColumnManager.load_from_json(config_path)
        return ColumnManager(self.column_default_definitions)

    def add_playlist_with_manager(self, playlist: Playlist) -> None:
        column_manager = ColumnManager(self.column_default_definitions)
        self.add_playlist(playlist, column_manager)

    def add_files(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Add Files", "", "All Files (*);;Audio Files (*.mp3 *.wav *.flac)"
        )
        if file_paths:
            current_index = self.tab_widget.currentIndex()
            if current_index != -1:
                playlist = self.playlist_manager.playlists[current_index]
                self.load_files(file_paths, playlist)

    def add_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "Add Folder", "")
        if folder_path:
            current_index = self.tab_widget.currentIndex()
            if current_index != -1:
                playlist = self.playlist_manager.playlists[current_index]
                file_paths = [folder_path]
                self.load_files(file_paths, playlist)

    def remove_missing_files(self) -> None:
        self.song_library.remove_missing_files()

    def clear_song_library(self) -> None:
        self.song_library.clear()

    def load_all_songs_from_library(self) -> None:
        songs = self.song_library.get_all_songs()
        for song in songs:
            id = song.id

            current_index = self.tab_widget.currentIndex()
            if current_index != -1:
                playlist = self.playlist_manager.playlists[current_index]
                playlist.add_song(id)

        self.update_playlist_view() 

    def load_files(self, file_paths: List[str], playlist: Playlist) -> None:
        file_fetcher = FileFetcher()
        file_list = file_fetcher.get_files_recursively_from_path_list(file_paths)

        self.ui_manager.progress_bar.show()

        self.total_files = len(file_list)
        self.files_remaining = self.total_files
        self.ui_manager.progress_bar.setMaximum(self.total_files)

        self.file_loader = FakeLoader(file_list)
        self.file_loader.set_song_loaded_callback(self.on_song_loaded)
        self.file_loader.set_all_songs_loaded_callback(self.on_all_songs_loaded)
        self.file_loader.start_loading()

        self.progress_bar_value_changed.connect(self.ui_manager.progress_bar.setValue)

    def on_song_loaded(self, song: Optional[Song]) -> None:
        if song is None:
            logger.error("Failed to load song.")
            return

        self.song_library.add_song(song)

        # current_index = self.tab_widget.currentIndex()
        # if current_index != -1:
        #     playlist = self.playlist_manager.playlists[current_index]
        #     playlist.add_song(song.id)

        self.files_remaining -= 1
        self.progress_bar_value_changed.emit(self.total_files - self.files_remaining)
        logger.info(f"Loaded song: {song.title} by {song.artist}")

    def on_all_songs_loaded(self) -> None:
        self.progress_bar_value_changed.emit(self.total_files)
        self.ui_manager.progress_bar.hide()
        logger.info("All songs have been loaded.")
        if self.file_loader:
            self.file_loader.all_songs_loaded_callback = None
            self.file_loader = None

        self.update_playlist_view()

    def update_playlist_view(self):
        playlist_tree_view = self.tab_widget.currentWidget()
        if isinstance(playlist_tree_view, PlaylistTreeView):
            playlist_tree_view.update_playlist_data()


if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
