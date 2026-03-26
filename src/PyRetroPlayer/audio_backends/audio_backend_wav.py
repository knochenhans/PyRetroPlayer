from __future__ import annotations

import os
import threading
import wave
from typing import Any, Dict, Optional

from loguru import logger

from PyRetroPlayer.audio_backends.audio_backend import AudioBackend


class AudioBackendWav(AudioBackend):
    def __init__(
        self,
        basepath: str = "/tmp/PyRetroPlayer_output",
        samplerate: int = 44100,
        buffersize: int = 512,
    ) -> None:
        self.basepath: str = basepath
        self.samplerate: int = samplerate
        self.buffersize: int = buffersize
        self.buffer: bytes = bytes(self.buffersize * 2 * 2)
        self.filename: str = "output.wav"

        self._lock = threading.RLock()
        self._closed: bool = False

        self._wave: Optional[wave.Wave_write] = None

        if not os.path.exists(self.basepath):
            os.makedirs(self.basepath)

        logger.debug(
            "WAV AudioBackend initialized with samplerate={} buffersize={} basepath={}",
            samplerate,
            buffersize,
            basepath,
        )

    def _init_file(self) -> None:
        try:
            self._wave = wave.open(os.path.join(self.basepath, self.filename), "wb")
            self._wave.setnchannels(2)
            self._wave.setsampwidth(2)  # 16-bit
            self._wave.setframerate(self.samplerate)

            self._closed = False
            self.buffer = bytes(self.buffersize * 2 * 2)  # stereo, 16-bit

            logger.debug("WAV file opened for writing.")
        except Exception as e:
            logger.error("Failed to open WAV file: {}", e)
            self._wave = None

    def write(self, data: bytes) -> None:
        if self._wave is None:
            self._init_file()
            if self._wave is None:
                logger.error("Cannot write to WAV file: initialization failed.")
            return

        with self._lock:
            if self._closed:
                return

            try:
                self._wave.writeframes(data)
            except Exception as e:
                logger.exception("Error writing audio data to WAV: {}", e)

    def reset(self) -> None:
        # WAV files don't support stream reset
        # logger.debug("Reset requested on WAV backend (ignored).")
        self.stop()

    def stop(self) -> None:
        with self._lock:
            self._closed = True

            try:
                if self._wave:
                    self._wave.close()
                    logger.debug("WAV file closed.")
            except Exception as e:
                logger.warning("Error while closing WAV backend: {}", e)
            finally:
                self._wave = None

    def close(self) -> None:
        self.stop()

    def get_buffer(self) -> bytes:
        return self.buffer

    def set_meta_data(self, meta_data: Dict[str, Any]) -> None:
        self.filename = f"{meta_data.get('title', 'output')}.wav"
        logger.debug("WAV backend meta data set: filename={}", self.filename)
