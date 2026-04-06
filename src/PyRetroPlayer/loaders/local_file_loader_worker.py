import weakref
from typing import Callable, Dict, List, Optional

from loguru import logger

from PyRetroPlayer.loaders.local_file_loader import LocalFileLoader
from PyRetroPlayer.loaders.module_tester import ModuleTester
from PyRetroPlayer.loaders.song_emitter import SongEmitter
from PyRetroPlayer.player_backends.player_backend import PlayerBackend
from PyRetroPlayer.playlist.loader_events import LoaderEvents
from PyRetroPlayer.playlist.song import Song


class LocalFileLoaderWorker:
    def __init__(
        self,
        song: Song,
        player_backends: Dict[str, Callable[[], PlayerBackend]],
        player_backends_priority: List[str],
        loader: "LocalFileLoader",
        events: LoaderEvents,
    ) -> None:
        self.song: Song = song
        self.player_backends: Dict[str, Callable[[], PlayerBackend]] = player_backends
        self.player_backends_priority: List[str] = player_backends_priority
        # keep weakref to avoid reference cycles / lifetime issues
        self.loader = weakref.ref(loader)
        self.events: LoaderEvents = events
        self.emitter = SongEmitter(
            self.song_checked_callback, self.song_info_retrieved_callback
        )

    def __call__(self) -> None:
        try:
            if self.song:
                tester = ModuleTester(
                    self.song,
                    self.player_backends,
                    self.player_backends_priority,
                    self.emitter,
                )
                tester.test_backends()
        except Exception:
            logger.exception(
                "Exception in LocalFileLoaderWorker for %s",
                getattr(self.song, "file_path", "<unknown>"),
            )
        finally:
            # Always notify loader that this song finished (success or failure)
            try:
                self.events.song_finished.emit()
            except Exception:
                logger.exception("Exception in loader.song_finished_loading()")

    def song_checked_callback(self, song: Optional[Song]) -> None:
        try:
            self.events.song_loaded.emit(song)
        except Exception:
            logger.exception("Exception in song_loaded_callback")

    def song_info_retrieved_callback(self, song: Song) -> None:
        try:
            self.events.song_info_retrieved.emit(song)
        except Exception:
            logger.exception("Exception in song_info_retrieved_callback")
