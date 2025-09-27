from typing import List, Optional

from loaders.abstract_loader import AbstractLoader  # type: ignore
from loaders.fake_loader import FakeLoader  # type: ignore
from loaders.file_fetcher import FileFetcher  # type: ignore
from loguru import logger
from main_window import MainWindow  # type: ignore
from playlist.playlist import Playlist  # type: ignore
from playlist.song import Song  # type: ignore


class FileManager:
    def __init__(self, main_window: "MainWindow") -> None:
        self.main_window = main_window
        self.file_loader = None
        self.total_files = 0
        self.files_remaining = 0

        self.loaders: List[type[AbstractLoader]] = [FakeLoader]

        # Sort loaders by priority (higher priority first)
        self.loaders.sort(key=lambda loader: loader.priority, reverse=True)

    def load_files(self, file_paths: List[str], playlist: Playlist) -> None:
        file_fetcher = FileFetcher()
        file_list = file_fetcher.get_files_recursively_from_path_list(file_paths)

        self.main_window.ui_manager.progress_bar.show()

        self.total_files = len(file_list)
        self.files_remaining = self.total_files
        self.main_window.ui_manager.progress_bar.setMaximum(self.total_files)

        for loader_class in self.loaders:
            loader_instance = loader_class(
                player_backends=self.main_window.player_backends
            )
            if all(loader_instance.try_loading_song(file) for file in file_list):
                self.file_loader = loader_instance
                logger.info(f"Using loader: {loader_class.__name__}")
                break

        if self.file_loader:
            self.file_loader.set_file_list(file_list)
            self.file_loader.set_song_loaded_callback(self.on_song_loaded)
            self.file_loader.set_all_songs_loaded_callback(self.on_all_songs_loaded)
            self.file_loader.start_loading()

        self.main_window.progress_bar_value_changed.connect(
            self.main_window.ui_manager.progress_bar.setValue
        )

    def on_song_loaded(self, song: Optional[Song]) -> None:
        if song is None:
            logger.error("Failed to load song.")
            return

        self.main_window.song_library.add_song(song)

        current_index = self.main_window.tab_widget.currentIndex()
        if current_index != -1:
            playlist = self.main_window.playlist_manager.playlists[current_index]
            playlist.add_song(song.id)

        self.files_remaining -= 1
        self.main_window.progress_bar_value_changed.emit(
            self.total_files - self.files_remaining
        )
        logger.info(f"Loaded song: {song.title} by {song.artist}")

    def on_all_songs_loaded(self) -> None:
        self.main_window.progress_bar_value_changed.emit(self.total_files)
        self.main_window.ui_manager.progress_bar.hide()
        logger.info("All songs have been loaded.")
        if self.file_loader:
            self.file_loader.all_songs_loaded_callback = None
            self.file_loader = None

        self.main_window.update_playlist_view()

    def load_all_songs_from_library(self) -> None:
        songs = self.main_window.song_library.get_all_songs()
        for song in songs:
            id = song.id

            current_index = self.main_window.tab_widget.currentIndex()
            if current_index != -1:
                playlist = self.main_window.playlist_manager.playlists[current_index]
                playlist.add_song(id)

        self.main_window.update_playlist_view()
