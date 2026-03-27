from PySide6.QtCore import QObject, Signal
from typing import Optional


class LoaderEvents(QObject):
    song_loaded = Signal(object)  # Optional[Song]
    all_songs_loaded = Signal()
    song_info_retrieved = Signal(object)  # Song
    song_finished = Signal()
