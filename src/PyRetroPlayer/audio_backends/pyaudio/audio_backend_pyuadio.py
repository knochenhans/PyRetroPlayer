import threading
import time
from typing import Optional

from loguru import logger
from pyaudio import PyAudio, Stream, get_format_from_width

from PyRetroPlayer.audio_backends.audio_backend import AudioBackend


class AudioBackendPyAudio(AudioBackend):
    def __init__(self, samplerate: int = 44100, buffersize: int = 512) -> None:
        self.samplerate: int = samplerate
        self.buffersize: int = buffersize
        self.buffer: bytes = bytes(self.buffersize * 2 * 2)

        self.p: Optional[PyAudio] = None
        self.stream: Optional[Stream] = None

        self._lock = threading.RLock()
        self._closed = False

        self._init_stream()
        logger.debug(
            "PyAudio AudioBackend initialized with samplerate: {} and buffersize: {}",
            samplerate,
            buffersize,
        )

    def _init_stream(self) -> None:
        try:
            self.p = PyAudio()
            self.stream = self.p.open(
                format=get_format_from_width(2),
                channels=2,
                rate=self.samplerate,
                output=True,
                frames_per_buffer=self.buffersize,
            )
            logger.debug("PyAudio stream successfully opened.")
        except Exception as e:
            logger.error("Failed to initialize PyAudio stream: {}", e)
            self.stream = None

    def _ensure_stream(self) -> bool:
        if self.stream is None or not self.stream.is_active():
            logger.warning("PyAudio stream invalid or closed — reinitializing.")
            self.close()
            self._init_stream()
            if self.stream is None:
                logger.error("Reinitialization failed — no stream available.")
                return False
        return True

    def write(self, data: bytes) -> None:
        if self.stream is None:
            logger.error("No active PyAudio stream available for writing.")
            return

        with self._lock:
            if self._closed or not self._ensure_stream():
                return
            try:
                self.stream.write(data)
            except OSError as e:
                logger.warning("PyAudio write error: {} — attempting recovery.", e)
                time.sleep(0.05)
                self._init_stream()
            except Exception as e:
                logger.exception("Unexpected error during PyAudio write: {}", e)

    def reset(self) -> None:
        if self.stream is None:
            logger.error("No active PyAudio stream available for reset.")
            return

        if not self._ensure_stream():
            return
        try:
            if self.stream.is_active():
                self.stream.stop_stream()
            self.stream.start_stream()
            logger.debug("PyAudio stream reset.")
        except Exception as e:
            logger.warning("Error resetting PyAudio stream: {}", e)
            self._init_stream()

    def stop(self) -> None:
        with self._lock:
            self._closed = True
            try:
                if self.stream:
                    if self.stream.is_active():
                        self.stream.stop_stream()
                    self.stream.close()
                if self.p:
                    self.p.terminate()
            except Exception as e:
                logger.warning("Error while stopping PyAudio backend: {}", e)
            finally:
                self.stream = None
                self.p = None

    def close(self) -> None:
        self.stop()

    def get_buffer(self) -> bytes:
        return self.buffer
