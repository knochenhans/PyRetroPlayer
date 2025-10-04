import threading
from typing import Callable, Optional

from loguru import logger

from PyRetroPlayer.playing_modes import ModArchiveSource, PlayingMode, PlayingSource
from PyRetroPlayer.playlist.song import Song
from PyRetroPlayer.web_helper import WebHelper


class ModArchiveRandomModuleFetcherThread(threading.Thread):
    def __init__(
        self,
        song: Song,
        current_playing_mode: PlayingMode,
        current_playing_source: PlayingSource,
        current_modarchive_source: ModArchiveSource,
        web_helper: WebHelper,
        artist_name: str | None = None,
        member_id: int | None = None,
        module_fetched_callback: Optional[Callable[[Song], None]] = None,
    ) -> None:
        super().__init__()
        self.song = song
        self.playing_mode = current_playing_mode
        self.playing_source = current_playing_source
        self.modarchive_source = current_modarchive_source
        self.web_helper = web_helper
        self.artist_name = artist_name
        self.member_id = member_id
        self.module_fetched_callback = module_fetched_callback
        self._terminate = threading.Event()

    def run(self) -> None:
        if self._terminate.is_set():
            logger.info("Thread terminated before run.")
            return
        self.fetch_random_module_id()
        if self.module_fetched_callback:
            self.module_fetched_callback(self.song)

    def fetch_random_module_id(self) -> None:
        id: Optional[int] = None

        if self.playing_mode == PlayingMode.RANDOM:
            if self.playing_source == PlayingSource.MODARCHIVE:
                match self.modarchive_source:
                    case ModArchiveSource.ALL:
                        logger.info("Getting random module")
                        id = self.web_helper.get_random_module_id()
                    case ModArchiveSource.FAVORITES:
                        if self.member_id:
                            logger.info("Getting random favorite module")
                            id = self.web_helper.get_random_favorite_module_id(
                                self.member_id
                            )
                    case ModArchiveSource.ARTIST:
                        if self.artist_name:
                            logger.info("Getting random artist module")
                            id = self.web_helper.get_random_artist_module_id(
                                self.artist_name
                            )
            if id:
                self.song.custom_metadata["modarchive_id"] = id

    def terminate(self) -> None:
        logger.info("Terminating ModArchiveRandomModuleFetcherThread")
        self._terminate.set()
