import threading
from typing import Callable, Optional

from loguru import logger

from PyRetroPlayer.loaders.module_loader_thread import ModuleLoaderThread
from PyRetroPlayer.playlist.song import Song
from PyRetroPlayer.web_helper import WebHelper


class ModArchiveDownloaderThread(ModuleLoaderThread):
    def __init__(
        self,
        web_helper: Optional[WebHelper] = None,
        song: Optional[Song] = None,
        temp_dir: Optional[str] = None,
        module_loaded_callback: Optional[Callable[[Song], None]] = None,
    ) -> None:
        super().__init__()
        self.web_helper = web_helper
        self.song = song
        self.temp_dir = temp_dir
        self.module_loaded_callback = module_loaded_callback
        self._terminate = threading.Event()

    def run(self) -> None:
        if self._terminate.is_set():
            logger.debug("Thread terminated before run.")
            return
        loaded_song = self.load_module()
        if loaded_song and self.module_loaded_callback:
            self.module_loaded_callback(loaded_song)

    def load_module(self) -> Optional[Song]:
        if self.web_helper:
            if self.temp_dir:
                if self.song:
                    filename = self.web_helper.download_module_file(
                        self.song.custom_metadata.get("modarchive_id", ""),
                        self.temp_dir,
                    )

                    if filename:
                        self.song.file_path = filename
                        self.song.is_ready = True
                        # self.song.modarchive_id = self.song.custom_metadata.get("modarchive_id", "")
                        return self.song
                else:
                    raise ValueError("Song ID not set")
            else:
                raise ValueError("Temporary directory not set")
        return None

    def terminate(self) -> None:
        logger.debug("Terminating ModArchiveDownloaderThread")
        self._terminate.set()
