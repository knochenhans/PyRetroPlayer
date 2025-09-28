import json
import os
import sys
from typing import Any, Dict, List, Optional

from appdirs import user_config_dir, user_data_dir  # type: ignore
from importlib_resources import files
from player_backends.fake_player_backend import FakePlayerBackend  # type: ignore
from playlist.column_manager import ColumnManager  # type: ignore
from playlist.playlist import Playlist  # type: ignore
from playlist.playlist_manager import PlaylistManager  # type: ignore
from playlist.playlist_tab_widget import PlaylistTabWidget  # type: ignore
from playlist.song import Song  # type: ignore
from playlist.song_library import SongLibrary  # type: ignore
from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
)
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

        default_columns_definitions = (
            files("data").joinpath("default_columns_configuration.json").read_text()
        )

        self.column_default_definitions: List[Dict[str, Any]] = json.loads(
            default_columns_definitions
        )

        from file_manager import FileManager  # type: ignore

        self.file_manager = FileManager(self)

        from playlist_ui_manager import PlaylistUIManager  # type: ignore

        self.playlist_ui_manager = PlaylistUIManager(self)

        self.tab_widget: PlaylistTabWidget = PlaylistTabWidget(
            self, self.playlist_manager
        )
        self.tab_widget.tab_added.connect(self.playlist_ui_manager.create_new_playlist)
        self.tab_widget.tab_deleted.connect(self.playlist_ui_manager.on_delete_playlist)
        self.ui_manager.add_widget(self.tab_widget)

        self.ui_manager.create_menu_bar()

        self.column_managers: Dict[str, ColumnManager] = {}

        self.song_library = SongLibrary(os.path.join(data_dir, "song_library.db"))

        # Load playlists and add tabs
        self.playlist_manager.load_playlists()
        for playlist in self.playlist_manager.playlists:
            self.playlist_ui_manager.add_playlist(
                playlist,
                self.playlist_ui_manager.load_or_create_column_manager(playlist),
            )

        # Create a new playlist if none exist
        if not self.playlist_manager.playlists:
            self.playlist_ui_manager.create_new_playlist()

        self.player_backends: Dict[str, Any] = {
            "FakeBackend": lambda: FakePlayerBackend()
        }

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

    def remove_missing_files(self) -> None:
        self.song_library.remove_missing_files()

    def clear_song_library(self) -> None:
        self.song_library.clear()

    def load_all_songs_from_library(self) -> None:
        self.file_manager.load_all_songs_from_library()

    def load_files(self, file_paths: List[str], playlist: Playlist) -> None:
        self.file_manager.load_files(file_paths, playlist)

    def on_song_loaded(self, song: Optional[Song]) -> None:
        self.file_manager.on_song_loaded(song)

    def on_all_songs_loaded(self) -> None:
        self.file_manager.on_all_songs_loaded()


if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
