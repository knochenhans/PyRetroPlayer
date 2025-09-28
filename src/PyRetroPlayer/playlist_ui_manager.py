import os

from icons import Icons  # type: ignore
from loguru import logger
from main_window import MainWindow  # type: ignore
from playlist.column_manager import ColumnManager  # type: ignore
from playlist.playlist import Playlist  # type: ignore
from playlist.playlist_tree_view import PlaylistTreeView  # type: ignore
from PySide6.QtWidgets import QFileDialog


class PlaylistUIManager:
    def __init__(self, main_window: "MainWindow") -> None:
        self.main_window = main_window
        self.playlist_manager = main_window.playlist_manager
        self.column_default_definitions = main_window.column_default_definitions

    def create_new_playlist(self) -> None:
        playlist = Playlist(name="New Playlist")
        self.playlist_manager.add_playlist(playlist)
        self.add_playlist_with_manager(playlist)

    def add_playlist(self, playlist: Playlist, column_manager: ColumnManager) -> None:
        icons = Icons(self.main_window.playlist_configuration, self.main_window.style())
        playlist_view = PlaylistTreeView(
            icons,
            self.main_window.playlist_configuration,
            playlist,
            column_manager,
            self.column_default_definitions,
            self.main_window.song_library,
            self.main_window,
        )

        playlist.name = playlist.name or ""
        self.main_window.tab_widget.addTab(playlist_view, playlist.name)
        self.main_window.column_managers[playlist.id] = column_manager

        playlist_view.files_dropped.connect(
            lambda file_paths: self.main_window.file_manager.load_files(
                file_paths, playlist
            )
        )

    def on_delete_playlist(self) -> None:
        current_index = self.main_window.tab_widget.currentIndex()
        if current_index != -1:
            self.main_window.tab_widget.on_tab_close(current_index)

    def import_playlist(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window, "Import Playlist", "", "JSON Files (*.json)"
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
        current_index = self.main_window.tab_widget.currentIndex()
        if current_index != -1:
            playlist = self.playlist_manager.playlists[current_index]
            file_path, _ = QFileDialog.getSaveFileName(
                self.main_window, "Export Playlist", "", "JSON Files (*.json)"
            )
            if file_path:
                self.playlist_manager.save_playlist(playlist, file_path)
                logger.info(f"Exported playlist: {playlist.name}")

    def add_playlist_with_manager(self, playlist: Playlist) -> None:
        column_manager = ColumnManager(self.column_default_definitions)
        self.add_playlist(playlist, column_manager)

    def load_or_create_column_manager(self, playlist: Playlist) -> ColumnManager:
        config_path = os.path.join(
            self.playlist_manager.playlists_path,
            "columns",
            f"{playlist.id}.json",
        )
        if os.path.exists(config_path):
            return ColumnManager.load_from_json(config_path)
        return ColumnManager(self.column_default_definitions)
