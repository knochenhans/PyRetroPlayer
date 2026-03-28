import struct
import threading

from loguru import logger
from SettingsManager import SettingsManager

from PyRetroPlayer.player_backends.player_backend import PlayerBackend
from PyRetroPlayer.player_events import PlayerEvents


class BasePlayerThread(threading.Thread):
    def __init__(
        self,
        player_backend: PlayerBackend,
        settings_manager: SettingsManager,
        events: PlayerEvents,
    ) -> None:
        super().__init__(daemon=True)  # daemon=True so it won’t block program exit
        self.player_backend = player_backend
        self.settings_manager = settings_manager
        self.events = events

        self.stop_flag: threading.Event = threading.Event()
        self.pause_flag: threading.Event = threading.Event()

        self.max_silence_length_ms = self.settings_manager.get(
            "max_silence_length", 10000
        )

        logger.debug("PlayerThread initialized")

    def stop(self) -> None:
        logger.debug("Stop signal received")
        self.stop_flag.set()

    def is_silent(self, buffer: bytes, threshold: int = 0) -> bool:
        samples = struct.iter_unpack("<h", buffer)  # 16-bit little endian
        return all(abs(sample[0]) <= threshold for sample in samples)
