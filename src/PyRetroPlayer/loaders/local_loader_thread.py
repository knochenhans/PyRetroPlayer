from typing import Optional

from loguru import logger

from PyRetroPlayer.loaders.module_loader_thread import ModuleLoaderThread
from PyRetroPlayer.playlist.song import Song


class LocalLoaderThread(ModuleLoaderThread):
    def __init__(self) -> None:
        super().__init__()

        self.file_path: Optional[str] = None

    def load_module(self) -> Optional[Song]:
        if self.file_path:
            song: Song = Song()
            song.file_path = self.file_path
            song.is_ready = True
            logger.info(f"Loading local module: {song.file_path}")
            return song
        return None
