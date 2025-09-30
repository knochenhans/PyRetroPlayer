from typing import Dict, Optional
from uuid import uuid4


class PlaylistEntry:
    def __init__(self, song_id: str, entry_id: Optional[str] = None):
        self.song_id = song_id
        self.entry_id = entry_id or str(uuid4())  # unique per row

    def to_dict(self):
        return {"song_id": self.song_id, "entry_id": self.entry_id}

    @staticmethod
    def from_dict(data: Dict[str, str]) -> "PlaylistEntry":
        return PlaylistEntry(song_id=data["song_id"], entry_id=data.get("entry_id"))
