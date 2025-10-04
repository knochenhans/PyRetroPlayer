from enum import Enum, auto


class PlayingMode(Enum):
    LINEAR = auto()
    RANDOM = auto()


class PlayingSource(Enum):
    LOCAL = auto()
    MODARCHIVE = auto()


class ModArchiveSource(Enum):
    ALL = auto()
    FAVORITES = auto()
    ARTIST = auto()


class LocalSource(Enum):
    PLAYLIST = auto()
    FOLDER = auto()
