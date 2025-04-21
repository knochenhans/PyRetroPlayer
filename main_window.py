import json
import os
import sys
from typing import Any, Dict, List

from appdirs import user_config_dir
from importlib_resources import files
from loguru import logger
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMenu,
    QMenuBar,
    QVBoxLayout,
    QWidget,
)

from icons import Icons
from playlist.column_manager import ColumnManager
from playlist.playlist import Playlist
from playlist.playlist_manager import PlaylistManager
from playlist.playlist_tab_widget import PlaylistTabWidget
from playlist.playlist_tree_view import PlaylistTreeView
from settings.settings import Settings


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.application_name: str = "PyRetroPlayer"
        self.application_version: str = "0.1.0"

        self.setWindowTitle(f"{self.application_name} v{self.application_version}")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.settings: Settings = Settings(
            "playlist_configuration",
            os.path.join(user_config_dir(), self.application_name),
        )
        self.settings.load()

        self.playlist_manager = PlaylistManager(self.application_name)

        self.tab_widget: PlaylistTabWidget = PlaylistTabWidget(
            self, self.playlist_manager
        )
        self.tab_widget.tab_added.connect(self.create_new_playlist)
        self.tab_widget.tab_deleted.connect(self.on_delete_playlist)
        layout.addWidget(self.tab_widget)

        self.create_menu_bar()

        default_columns_definitions = (
            files("data").joinpath("default_columns_configuration.json").read_text()
        )

        if isinstance(default_columns_definitions, str):
            self.column_default_definitions: List[Dict[str, Any]] = json.loads(
                default_columns_definitions
            )

        self.column_managers: dict[str, ColumnManager] = {}

        # Load playlists and add tabs
        self.playlist_manager.load_playlists()
        for playlist in self.playlist_manager.playlists:
            config_path = os.path.join(
                self.playlist_manager.playlists_path,
                "columns",
                f"{playlist.id}.json",
            )
            if os.path.exists(config_path):
                column_manager = ColumnManager.load_from_json(config_path)
            else:
                column_manager = ColumnManager(self.column_default_definitions)
            self.add_playlist(playlist, column_manager)

    def create_menu_bar(self) -> None:
        menu_bar: QMenuBar = self.menuBar()

        file_menu: QMenu = menu_bar.addMenu("&File")

        new_playlist_action: QAction = QAction("&New Playlist", self)
        new_playlist_action.triggered.connect(self.create_new_playlist)
        file_menu.addAction(new_playlist_action)

        import_action: QAction = QAction("&Import Playlist", self)
        import_action.triggered.connect(self.import_playlist)
        file_menu.addAction(import_action)

        export_action: QAction = QAction("&Export Playlist", self)
        export_action.triggered.connect(self.export_playlist)
        file_menu.addAction(export_action)

        delete_playlist_action: QAction = QAction("&Delete Playlist", self)
        delete_playlist_action.triggered.connect(self.on_delete_playlist)
        file_menu.addAction(delete_playlist_action)

        file_menu.addSeparator()

        exit_action: QAction = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def create_new_playlist(self) -> None:
        playlist = Playlist(name="New Playlist")
        self.playlist_manager.add_playlist(playlist)
        column_manager = ColumnManager(self.column_default_definitions)
        self.add_playlist(playlist, column_manager)

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
                column_manager = ColumnManager(self.column_default_definitions)
                self.add_playlist(playlist, column_manager)
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

        columns_dir = os.path.join(self.playlist_manager.playlists_path, "columns")
        os.makedirs(columns_dir, exist_ok=True)

        for playlist_id, column_manager in self.column_managers.items():
            config_path = os.path.join(
                self.playlist_manager.playlists_path,
                "columns",
                f"{playlist_id}.json",
            )
            column_manager.save_to_json(config_path)
        event.accept()

    def add_playlist(self, playlist: Playlist, column_manager: ColumnManager) -> None:
        icons = Icons(self.settings, self.style())
        playlist_view = PlaylistTreeView(
            icons,
            self.settings,
            playlist,
            column_manager,
            self.column_default_definitions,
            self,
        )

        playlist.name = playlist.name or ""
        self.tab_widget.addTab(playlist_view, playlist.name)
        self.column_managers[playlist.id] = column_manager


if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
