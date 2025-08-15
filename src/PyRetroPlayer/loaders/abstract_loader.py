from typing import Callable, Dict, Optional

from loguru import logger

from player_backends.player_backend import PlayerBackend
from playlist.song import Song


class AbstractLoader:
    def __init__(self, player_backends: Dict[str, Callable[[], PlayerBackend]]) -> None:
        self.player_backends = player_backends
        self.song_loaded_callback: Optional[Callable[[Optional[Song]], None]] = None
        self.all_songs_loaded_callback: Optional[Callable[[], None]] = None

    def set_song_loaded_callback(
        self, callback: Callable[[Optional[Song]], None]
    ) -> None:
        self.song_loaded_callback = callback

    def set_all_songs_loaded_callback(self, callback: Callable[[], None]) -> None:
        self.all_songs_loaded_callback = callback

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
            if player_backend is not None:
                player_backend.song = song
                if player_backend.check_module():
                    logger.debug(f"Module loaded with player backend: {backend_name}")
                    song.backend_name = backend_name
                    player_backend.song = song
                    player_backend.retrieve_song_info()
                    return player_backend.song
        return None
