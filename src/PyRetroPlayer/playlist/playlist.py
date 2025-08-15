import uuid
from typing import List, Optional

from playlist.song import Song  # type: ignore
from playlist.song_library import SongLibrary  # type: ignore


class Playlist:
    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        song_ids: Optional[List[str]] = None,
    ) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.name = name
        self.song_ids = song_ids or []

    def add_song(self, song_id: str) -> None:
        if song_id not in self.song_ids:
            self.song_ids.append(song_id)

    def remove_song(self, song_id: str) -> None:
        if song_id in self.song_ids:
            self.song_ids.remove(song_id)

    def get_songs(self) -> List[str]:
        return self.song_ids

    def get_song_metadata(self, song_library: SongLibrary) -> List[Song]:
        return [
            song
            for song in (song_library.get_song(song_id) for song_id in self.song_ids)
            if song is not None
        ]
