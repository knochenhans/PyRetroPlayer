import threading
import time
from typing import Callable, Optional

from audio_backends.audio_backend import AudioBackend  # type: ignore
from loguru import logger
from player_backends.player_backend import PlayerBackend  # type: ignore


class PlayerThread(threading.Thread):
    def __init__(
        self,
        player_backend: PlayerBackend,
        audio_backend: AudioBackend,
        on_position_changed: Optional[Callable[[int, int], None]] = None,
        on_song_finished: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(daemon=True)  # daemon=True so it won’t block program exit
        self.player_backend = player_backend
        self.audio_backend = audio_backend
        self.on_position_changed = on_position_changed
        self.on_song_finished = on_song_finished
        self.stop_flag = threading.Event()
        self.pause_flag = threading.Event()
        logger.debug("PlayerThread initialized")

    def run(self) -> None:
        self.player_backend.prepare_playing()
        module_length = self.player_backend.get_module_length()
        logger.debug("Module length: {} milliseconds", module_length)

        count: int = 0

        while not self.stop_flag.is_set():
            if self.pause_flag.is_set():
                time.sleep(0.1)
                continue

            count, buffer = self.player_backend.read_chunk(
                self.audio_backend.samplerate, self.audio_backend.buffersize
            )
            if count == 0:
                logger.debug("End of module reached")
                break

            self.audio_backend.write(buffer)

            current_position = self.player_backend.get_position_milliseconds()
            if not self.stop_flag.is_set() and self.on_position_changed:
                self.on_position_changed(current_position, module_length)

        if count == 0 and self.on_song_finished:
            self.on_song_finished()
            logger.debug("Song finished")

        self.player_backend.free_module()
        logger.debug("Playback stopped")

    def stop(self) -> None:
        logger.debug("Stop signal received")
        self.stop_flag.set()

    def pause(self) -> None:
        if self.pause_flag.is_set():
            self.pause_flag.clear()
        else:
            self.pause_flag.set()
        logger.debug("Pause toggled: {}", self.pause_flag.is_set())

    def seek(self, position: int) -> None:
        logger.debug("Seeking to position: {}", position)
        self.player_backend.seek(position)
