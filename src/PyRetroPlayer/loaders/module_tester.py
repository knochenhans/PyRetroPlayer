from typing import Callable, Dict, List

from loguru import logger

from PyRetroPlayer.loaders.song_emitter import SongEmitter
from PyRetroPlayer.player_backends.player_backend import PlayerBackend
from PyRetroPlayer.playlist.song import Song


class ModuleTester:
    def __init__(
        self,
        song: Song,
        player_backends: Dict[str, Callable[[], PlayerBackend]],
        player_backends_priority: List[str],
        emitter: SongEmitter,
    ):
        self.song = song
        self.player_backends = player_backends
        self.player_backends_priority = player_backends_priority
        self.emitter = emitter

    def test_backends(self) -> None:
        sorted_backend_names = [
            name
            for name in self.player_backends_priority
            if name in self.player_backends
        ]
        sorted_backend_names += [
            name for name in self.player_backends if name not in sorted_backend_names
        ]
        self.song.available_backends = []
        info_retrieved = False
        for backend_name in sorted_backend_names:
            backend_factory = self.player_backends[backend_name]
            logger.debug(f"Trying player backend: {backend_name}")

            player_backend = backend_factory()
            player_backend.song = self.song
            if player_backend.check_module():
                self.song.available_backends.append(backend_name)
                if not info_retrieved:
                    player_backend.retrieve_song_info()
                    self.song = player_backend.song
                    self.emitter.song_info_retrieved(self.song)
                    info_retrieved = True
            try:
                player_backend.cleanup()
            except Exception:
                logger.exception("Error during backend.cleanup()")

        if not self.song.available_backends:
            self.song.available_backends = []
            logger.warning(
                f"No available backends found for song: {self.song.file_path}, song cannot be played."
            )
            self.emitter.song_checked(None)
            return
        self.emitter.song_checked(self.song)
