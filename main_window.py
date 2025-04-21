import json
import os
import sys
from typing import Any, Dict, List

from appdirs import user_config_dir, user_data_dir
from importlib_resources import files
from loguru import logger
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
)

from icons import Icons
from playlist.column_manager import ColumnManager
from playlist.playlist import Playlist
from playlist.playlist_manager import PlaylistManager
from playlist.playlist_tab_widget import PlaylistTabWidget
from playlist.playlist_tree_view import PlaylistTreeView
from playlist.song import Song
from playlist.song_library import SongLibrary
from settings.settings import Settings
from ui_manager import UIManager


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.application_name: str = "PyRetroPlayer"
        self.application_version: str = "0.1.0"

        self.setWindowTitle(f"{self.application_name} v{self.application_version}")

        self.ui_manager = UIManager(self)

        layout = self.ui_manager.setup_central_widget()

        config_dir = os.path.join(user_config_dir(), self.application_name)
        os.makedirs(config_dir, exist_ok=True)

        data_dir = os.path.join(user_data_dir(), self.application_name)
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
        layout.addWidget(self.tab_widget)

        self.ui_manager.create_menu_bar()

        default_columns_definitions = (
            files("data").joinpath("default_columns_configuration.json").read_text()
        )

        if isinstance(default_columns_definitions, str):
            self.column_default_definitions: List[Dict[str, Any]] = json.loads(
                default_columns_definitions
            )

        self.column_managers: dict[str, ColumnManager] = {}

        # Load playlists and add tabs
        # self.playlist_manager.load_playlists()
        # for playlist in self.playlist_manager.playlists:
        #     column_manager = self.load_or_create_column_manager(playlist)
        #     self.add_playlist(playlist, column_manager)

        self.song_library = SongLibrary(os.path.join(data_dir, "song_library.db"))

        # Example songs
        example_songs = [
            Song(title="song1.mp3", file_path="path/to/song1.mp3", artist="Artist 1"),
            Song(title="song2.mp3", file_path="path/to/song2.mp3", artist="Artist 2"),
        ]
        # for song in example_songs:
        #     self.song_library.add_song(song)

        playlist = Playlist(
            id="example_playlist",
            name="Example Playlist",
        )

        for song in self.song_library.get_all_songs():
            playlist.add_song(song.id)

        column_manager = self.load_or_create_column_manager(playlist)
        self.add_playlist(playlist, column_manager)

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

    def closeEvent(self, event) -> None:
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
                # playlist.add_songs(file_paths)
                logger.info(f"Added files to playlist: {playlist.name}")

    def add_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "Add Folder", "")
        if folder_path:
            # Collect all audio files in the folder
            audio_files = []
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.endswith((".mp3", ".wav", ".flac")):
                        audio_files.append(os.path.join(root, file))

            if audio_files:
                current_index = self.tab_widget.currentIndex()
                if current_index != -1:
                    playlist = self.playlist_manager.playlists[current_index]
                    # playlist.add_songs(audio_files)
                    logger.info(f"Added folder to playlist: {playlist.name}")


if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
