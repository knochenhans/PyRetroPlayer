import threading
import time
from random import uniform
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
)

from PyRetroPlayer.loaders.abstract_loader import AbstractLoader
from PyRetroPlayer.loaders.file_fetcher import FileFetcher
from PyRetroPlayer.loaders.local_file_loader import LocalFileLoader
from PyRetroPlayer.loaders.modarchive_downloader_thread import (
    ModArchiveDownloaderThread,
)
from PyRetroPlayer.loaders.modarchive_random_module_fetcher import (
    ModArchiveRandomModuleFetcherThread,
)
from PyRetroPlayer.main_window import MainWindow
from PyRetroPlayer.playing_modes import ModArchiveSource, PlayingMode, PlayingSource
from PyRetroPlayer.playlist.playlist import Playlist
from PyRetroPlayer.playlist.song import Song
from PyRetroPlayer.web_helper import WebHelper


class FileManager:
    def __init__(self, main_window: "MainWindow") -> None:
        self.main_window = main_window
        self.file_loader: Optional[AbstractLoader] = None
        self.total_files = 0
        self.files_remaining = 0
        self.web_helper = WebHelper()
        self.session = requests.Session()

        self.loaders: List[type[AbstractLoader]] = [LocalFileLoader]
        self.random_song: Optional[Song] = None
        self.random_module_fetcher_threads: List[
            ModArchiveRandomModuleFetcherThread
        ] = []

    def get_current_playlist(self) -> Optional[Playlist]:
        current_index = self.main_window.playlist_ui_manager.tab_widget.currentIndex()
        if current_index != -1:
            return self.main_window.playlist_ui_manager.playlist_manager.playlists[
                current_index
            ]
        return None

    def load_files(self, file_paths: List[str], playlist: Playlist) -> None:
        file_fetcher = FileFetcher()
        file_list = file_fetcher.get_files_recursively_from_path_list(file_paths)

        progress_bar = self.main_window.ui_manager.progress_bar

        self.total_files = len(file_list)
        self.files_remaining = self.total_files

        if self.total_files > 1:
            progress_bar.show()
            progress_bar.setMaximum(self.total_files)
            self.main_window.progress_bar_value_changed.connect(progress_bar.setValue)

        loader_instance = self.loaders[0](
            player_backends=self.main_window.player_backends,
            player_backends_priority=self.main_window.player_backends_priorities,
        )
        self.file_loader = loader_instance

        if self.file_loader:
            self.file_loader.set_file_list(file_list)
            self.file_loader.set_song_loaded_callback(self.on_song_loaded)
            self.file_loader.set_all_songs_loaded_callback(self.on_all_songs_loaded)
            self.file_loader.start_loading()

    def on_song_loaded(self, song: Optional[Song]) -> None:
        if song is None:
            logger.error("Failed to load song.")
            return

        id = self.main_window.song_library.add_song(song)
        playlist = self.get_current_playlist()
        if playlist:
            playlist.add_song(id)

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
            self.file_loader.cleanup()
            self.file_loader = None

        # self.main_window.update_playlist_view()

    def load_all_songs_from_library(self) -> None:
        songs = self.main_window.song_library.get_all_songs()
        playlist = self.get_current_playlist()
        for song in songs:
            id = song.id
            if playlist:
                playlist.add_song(id)
        # self.main_window.update_playlist_view()

    def add_files(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.main_window,
            "Add Files",
            "",
            "All Files (*);;Audio Files (*.mp3 *.wav *.flac)",
        )
        if file_paths:
            playlist = self.get_current_playlist()
            if playlist:
                self.load_files(file_paths, playlist)

    def add_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(
            self.main_window, "Add Folder", ""
        )
        if folder_path:
            playlist = self.get_current_playlist()
            if playlist:
                file_paths = [folder_path]
                self.load_files(file_paths, playlist)

    def get_random_module(self) -> None:
        # Ask user for number of tracks to load
        num_tracks, ok = QInputDialog.getInt(
            self.main_window,
            "Load Random Modules",
            "How many random tracks do you want to load?",
            1,  # default value
            1,  # min value
            100,  # max value
            1,  # step
        )
        if not ok:
            return

        # Run the fetching and loading in a background thread
        thread = threading.Thread(
            target=self._fetch_and_load_random_modules, args=(num_tracks,)
        )
        thread.start()

    def _fetch_and_load_random_modules(self, num_tracks: int) -> None:
        fetched_songs: List[Song] = []
        for _ in range(num_tracks):
            song = Song()
            playing_mode: PlayingMode = PlayingMode.RANDOM
            playing_source: PlayingSource = PlayingSource.MODARCHIVE
            modarchive_source: ModArchiveSource = ModArchiveSource.ALL

            random_module_fetcher_thread = ModArchiveRandomModuleFetcherThread(
                song,
                playing_mode,
                playing_source,
                modarchive_source,
                self.web_helper,
            )
            self.random_module_fetcher_threads.append(random_module_fetcher_thread)
            random_module_fetcher_thread.start()
            random_module_fetcher_thread.join()  # Wait for thread to finish

            logger.debug(
                f"Random module fetched, ModArchive ID: {song.custom_metadata.get('modarchive_id', None)}"
            )

            self.random_module_fetcher_threads = [
                thread
                for thread in self.random_module_fetcher_threads
                if thread.is_alive()
            ]

            fetched_songs.append(song)

            time.sleep(uniform(0.5, 2.0))

        for song in fetched_songs:
            modarchive_downloader_thread = ModArchiveDownloaderThread(
                web_helper=self.web_helper, song=song, temp_dir="/tmp/PyRetroPlayer"
            )
            modarchive_downloader_thread.start()
            modarchive_downloader_thread.join()  # Wait for thread to finish

            if song and song.is_ready:
                playlist = self.get_current_playlist()
                if playlist:
                    self.load_files([song.file_path], playlist)
            time.sleep(uniform(0.5, 2.0))

    def safe_get(
        self, url: str, **kwargs: Dict[str, Any]
    ) -> Optional[requests.Response]:
        try:
            response = self.session.get(url, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def rescan_song(self, song: Song) -> Optional[Song]:
        if not song or not song.file_path:
            return None

        backend_name = song.available_backends[0] if song.available_backends else None

        if backend_name is None:
            return None
        
        backend = self.main_window.player_backends.get(backend_name)

        if backend is None:
            return None
        
        backend_instance = backend()
        backend_instance.song = song
        if backend_instance.check_module():
            backend_instance.retrieve_song_info()
            return backend_instance.song
        return None
