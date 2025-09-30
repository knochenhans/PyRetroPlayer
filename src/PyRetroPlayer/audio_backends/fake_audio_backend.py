from audio_backends.audio_backend import AudioBackend  # type: ignore
from typing import Any
from loguru import logger


class FakeAudioBackend(AudioBackend):
    def __init__(self, samplerate: int, buffersize: int) -> None:
        super().__init__(samplerate, buffersize)
        self.buffer = bytearray()  # Simulated audio buffer
        self.is_playing = False

    def write(self, data: bytes) -> None:
        self.buffer.extend(data)
        self.is_playing = True
        logger.debug(f"FakeAudioBackend: Writing {len(data)} bytes to buffer.")

    def stop(self) -> None:
        self.is_playing = False
        logger.debug("FakeAudioBackend: Stopping playback.")

    def get_buffer(self) -> Any:
        logger.debug(f"FakeAudioBackend: Returning buffer of size {len(self.buffer)}.")
        return self.buffer
