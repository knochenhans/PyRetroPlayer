from typing import Callable, Dict, List, Optional

from loguru import logger
from player_backends.player_backend import PlayerBackend  # type: ignore
from playlist.song import Song  # type: ignore


class AbstractLoader:
    def __init__(
        self,
        player_backends: Dict[str, Callable[[], PlayerBackend]],
        player_backends_priority: List[str],
    ) -> None:
        self.player_backends = player_backends
        self.player_backends_priority = player_backends_priority
        self.song_loaded_callback: Optional[Callable[[Optional[Song]], None]] = None
        self.song_info_retrieved_callback: Optional[
            Callable[[Optional[Song]], None]
        ] = None
        self.all_songs_loaded_callback: Optional[Callable[[], None]] = None

        self.reset()

    def reset(self) -> None:
        self.file_list: List[str] = []
        self.songs_to_load = 0
        self.songs_loaded = 0
        self.song_loaded_callback = None
        self.all_songs_loaded_callback = None

    def set_file_list(self, file_list: List[str]) -> None:
        self.reset()
        self.file_list = file_list
        self.songs_to_load = len(file_list)

    def set_song_loaded_callback(
        self, callback: Callable[[Optional[Song]], None]
    ) -> None:
        self.song_loaded_callback = callback

    def set_all_songs_loaded_callback(self, callback: Callable[[], None]) -> None:
        self.all_songs_loaded_callback = callback

    def try_loading_song(self, file_path: str) -> bool:
        # Check if file exists and is readable
        try:
            with open(file_path, "rb"):
                pass
        except (FileNotFoundError, IOError) as e:
            logger.error(f"File not found or unreadable: {file_path}, error: {e}")
            return False
        return True

    def start_loading(self) -> None:
        if not self.file_list:
            logger.warning("No files to load.")
            return

        logger.info("Starting to load files...")
        self.load_songs()

    def load_song(self, file_path: str) -> Optional[Song]:
        return None

    def load_songs(self) -> None:
        pass

    def on_song_loaded(self, song: Optional[Song]) -> None:
        if self.song_loaded_callback:
            self.song_loaded_callback(song)

    def update_song_info(self, song: Song) -> Optional[Song]:
        # Try to load the module by going through the available player backends
        for backend_name, backend_factory in self.player_backends.items():
            logger.debug(f"Trying player backend: {backend_name}")

            player_backend = backend_factory()
            player_backend.song = song
            if player_backend.check_module():
                logger.debug(f"Module loaded with player backend: {backend_name}")
                song.available_backends = backend_name
                player_backend.song = song
                player_backend.retrieve_song_info()
                return player_backend.song
        return None

    def all_songs_loaded(self) -> None:
        logger.info("All songs have been loaded.")

        if self.all_songs_loaded_callback:
            self.all_songs_loaded_callback()  #

    def song_finished_loading(self) -> None:
        self.songs_loaded += 1
        if self.songs_loaded >= self.songs_to_load:
            self.all_songs_loaded()
