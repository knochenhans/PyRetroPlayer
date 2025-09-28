import threading
import time
from typing import Callable, Dict, List, Optional

from loaders.abstract_loader import AbstractLoader  # type: ignore
from loguru import logger
from player_backends.player_backend import PlayerBackend  # type: ignore
from playlist.song import Song  # type: ignore


class FakeLoader(AbstractLoader):
    priority = 10

    def __init__(self, player_backends: Dict[str, Callable[[], PlayerBackend]]) -> None:
        super().__init__(player_backends)

        self.loading_thread: Optional[threading.Thread] = None

    def reset(self) -> None:
        self.loading_thread = None
        return super().reset()

    def start_loading(self) -> None:
        self.loading_thread = threading.Thread(target=self.load_songs)
        self.loading_thread.start()

    def load_songs(self) -> None:
        for file_path in self.file_list:
            song = self.load_song(file_path)
            if song:
                self.songs_loaded += 1
            time.sleep(0.1)  # Simulate some loading time
        if self.songs_loaded == self.songs_to_load:
            self.all_songs_loaded()

    def load_song(self, file_path: str) -> Optional[Song]:
        logger.debug(f"FakeLoader: Loading file: {file_path}")

        song: Optional[Song] = Song()

        if file_path and song:
            song.file_path = file_path
            song.title = file_path.split("/")[-1]
            song.artist = "Unknown Artist"
            song.backend_name = "FakeBackend"
            song.duration = 180  # Fake duration of 3 minutes
            song.is_ready = True

        self.on_song_loaded(song)
        return song

    def update_song_info(self, song: Song) -> Optional[Song]:
        logger.debug(f"FakeLoader: Retrieving filename for song: {song.file_path}")
        song.title = song.file_path.split("/")[-1]  # Extract filename as the title
        return song
