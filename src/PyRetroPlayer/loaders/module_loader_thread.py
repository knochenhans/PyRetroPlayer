import threading
from abc import abstractmethod
from typing import Callable, Optional

from PyRetroPlayer.playlist.song import Song


class ModuleLoaderThread(threading.Thread):
    def __init__(
        self,
        module_loaded_callback: Optional[Callable[[Song], None]] = None,
    ) -> None:
        super().__init__()
        self.module_loaded_callback = module_loaded_callback
        self._terminate = threading.Event()

    def run(self) -> None:
        if self._terminate.is_set():
            return
        song: Optional[Song] = self.load_module()
        if song and self.module_loaded_callback:
            self.module_loaded_callback(song)

    @abstractmethod
    def load_module(self) -> Optional[Song]:
        pass

    def terminate(self) -> None:
        self._terminate.set()
