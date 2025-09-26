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

    @staticmethod
    def load_playlist(file_path: str) -> Optional["Playlist"]:
        try:
            with open(file_path, "r") as f:
                playlist_data = json.load(f)
                logger.info(f"Loaded playlist: {playlist_data['name']}")
                return Playlist(
                    id=playlist_data["id"],
                    name=playlist_data["name"],
                    song_ids=playlist_data["song_ids"],
                )
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            logger.error(f"Failed to load playlist from {file_path}: {e}")
            return None

    @staticmethod
    def save_playlist(playlist: "Playlist", file_path: str) -> None:
        try:
            with open(file_path, "w") as f:
                json.dump(
                    {
                        "id": playlist.id,
                        "name": playlist.name,
                        "song_ids": playlist.get_songs(),
                    },
                    f,
                    indent=4,
                )
            logger.info(f"Playlist saved to {file_path}")
        except IOError as e:
            logger.error(f"Failed to save playlist to {file_path}: {e}")
