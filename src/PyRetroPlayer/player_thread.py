import threading
import time
from typing import Callable, Optional

from loguru import logger
from SettingsManager import SettingsManager

from PyRetroPlayer.audio_backends.audio_backend import AudioBackend
from PyRetroPlayer.player_backends.player_backend import PlayerBackend


class PlayerThread(threading.Thread):
    def __init__(
        self,
        player_backend: PlayerBackend,
        audio_backend: AudioBackend,
        settings_manager: SettingsManager,
        on_position_changed: Optional[Callable[[int, int], None]] = None,
        on_song_finished: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(daemon=True)  # daemon=True so it won’t block program exit
        self.player_backend = player_backend
        self.audio_backend = audio_backend
        self.on_position_changed = on_position_changed
        self.on_song_finished = on_song_finished
        self.settings_manager = settings_manager

        self.stop_flag = threading.Event()
        self.pause_flag = threading.Event()

        self.max_silence_length_ms = (
            self.settings_manager.get("max_silence_length", 10000)
        )

        logger.debug("PlayerThread initialized")

    def run(self) -> None:
        self.player_backend.prepare_playing()
        module_length = self.player_backend.get_module_length()
        logger.debug("Module length: {} milliseconds", module_length)

        count: int = 0

        silence_length_ms: float = 0.0

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

            # check if only contains silence
            if all(sample == 0 for sample in buffer):
                silence_length_ms += (
                    len(buffer) / (self.audio_backend.samplerate * 2) * 1000
                )
                if silence_length_ms > self.max_silence_length_ms:
                    logger.debug(
                        "Max silence length exceeded ({} ms), stopping playback",
                        self.max_silence_length_ms,
                    )
                    count = 0
                    break
            else:
                silence_length_ms = 0

            self.audio_backend.write(buffer)

            current_position = self.player_backend.get_position_milliseconds()
            if not self.stop_flag.is_set() and self.on_position_changed:
                self.on_position_changed(current_position, module_length)

        if count == 0 and self.on_song_finished:
            self.on_song_finished()
            logger.debug("Song finished")

        self.audio_backend.reset()

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
