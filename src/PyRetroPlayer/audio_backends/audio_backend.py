from abc import ABC, abstractmethod
from typing import Any, Dict


class AudioBackend(ABC):
    def __init__(self, samplerate: int, buffersize: int) -> None:
        self.samplerate: int = samplerate
        self.buffersize: int = buffersize

    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def write(self, data: bytes) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def get_buffer(self) -> Any:
        pass

    @abstractmethod
    def set_meta_data(self, meta_data: Dict[str, Any]) -> None:
        pass
