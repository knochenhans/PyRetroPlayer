from typing import Callable, Optional

from PyRetroPlayer.playlist.song import Song


class SongEmitter:
    def __init__(
        self,
        song_checked: Callable[[Optional[Song]], None],
        song_info_retrieved: Callable[[Song], None],
    ):
        self.song_checked = song_checked
        self.song_info_retrieved = song_info_retrieved
