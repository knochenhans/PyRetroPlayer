import json
import os
from typing import Any, Dict, List

from importlib_resources import files
from loguru import logger
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog

from PyRetroPlayer.actions_manager import ActionsManager
from PyRetroPlayer.main_window import MainWindow
from PyRetroPlayer.playlist.column_manager import ColumnManager
from PyRetroPlayer.playlist.playlist import Playlist
from PyRetroPlayer.playlist.playlist_manager import PlaylistManager
from PyRetroPlayer.playlist.playlist_tab_widget import PlaylistTabWidget
from PyRetroPlayer.playlist.playlist_tree_view import PlaylistTreeView
from PyRetroPlayer.settings.settings import Settings


class PlaylistUIManager:
    def __init__(self, main_window: "MainWindow") -> None:
        self.main_window = main_window
        self.playlist_configuration: Settings = Settings(
            "playlist_configuration",
            main_window.config_dir,
            self.main_window.application_name,
        )
        self.playlist_configuration.ensure_default_config()
        self.playlist_configuration.load()

        self.column_default_definitions: List[Dict[str, Any]] = json.loads(
            files("PyRetroPlayer.data").joinpath("default_columns_configuration.json").read_text()
        )

        self.column_managers: Dict[str, ColumnManager] = {}
        self.playlist_manager = PlaylistManager(self.main_window.application_name)

        self.tab_widget: PlaylistTabWidget = PlaylistTabWidget(
            self.main_window, self.playlist_manager
        )
        self.tab_widget.tab_added.connect(self.create_new_playlist)
        self.tab_widget.tab_deleted.connect(self.on_delete_playlist)
        self.main_window.ui_manager.add_widget(self.tab_widget)

        # Load playlists and add tabs
        self.playlist_manager.load_playlists()
        for playlist in self.playlist_manager.playlists:
            self.add_playlist(
                playlist,
                self.load_or_create_column_manager(playlist),
            )

        # Create a new playlist if none exist
        if not self.playlist_manager.playlists:
            self.create_new_playlist()

        self.current_tree_view = self.tab_widget.currentWidget()

    def create_new_playlist(self) -> None:
        playlist = Playlist(name="New Playlist")
        self.playlist_manager.add_playlist(playlist)
        self.add_playlist_with_manager(playlist)

    def add_playlist(self, playlist: Playlist, column_manager: ColumnManager) -> None:
        playlist_view = PlaylistTreeView(
            self.playlist_configuration,
            playlist,
            column_manager,
            self.column_default_definitions,
            self.main_window.song_library,
            self.main_window,
        )

        playlist.name = playlist.name or ""
        self.tab_widget.addTab(playlist_view, playlist.name)
        self.column_managers[playlist.id] = column_manager
        playlist_view.item_double_clicked.connect(
            lambda index: self.on_playlist_item_double_clicked(index, playlist_view)
        )

        playlist_view.files_dropped.connect(
            lambda file_paths: self.main_window.file_manager.load_files(
                file_paths, playlist
            )
        )

    def on_delete_playlist(self) -> None:
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            self.tab_widget.on_tab_close(current_index)

    def import_playlist(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window, "Import Playlist", "", "JSON Files (*.json)"
        )
        if file_path:
            playlist = Playlist.load_playlist(file_path)
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
                self.main_window, "Export Playlist", "", "JSON Files (*.json)"
            )
            if file_path:
                Playlist.save_playlist(playlist, file_path)
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

    def on_playlist_item_double_clicked(
        self, index: int, tree_view: PlaylistTreeView
    ) -> None:
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            playlist = self.playlist_manager.playlists[current_index]
            self.main_window.player_control_manager.play_song_from_index(
                index, playlist
            )
            tree_view.set_currently_playing_row(index)

    def setup_actions(self) -> None:
        actions: List[QAction] = ActionsManager.get_actions_by_names(
            self.main_window,
            ["song_info_dialog"],
        )
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, PlaylistTreeView):
                for action in actions:
                    action.setParent(widget)
                    widget.addAction(action)
