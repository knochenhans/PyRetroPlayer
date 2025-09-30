import json
import uuid
from typing import Callable, List, Optional

from loguru import logger

from playlist.playlist_entry import PlaylistEntry  # type: ignore
from playlist.song_library import SongLibrary  # type: ignore


class Playlist:
    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        entries: Optional[List[PlaylistEntry]] = None,
    ) -> None:
        self.id = id if id else str(uuid.uuid4())
        self.name = name
        self.entries = entries or []
        self.song_added: Optional[Callable[[PlaylistEntry], None]] = None
        self.song_removed: Optional[Callable[[PlaylistEntry], None]] = None
        self.current_song_index: int = -1

    def add_song(self, song_id: str) -> None:
        entry = PlaylistEntry(song_id)
        self.entries.append(entry)
        if self.song_added:
            self.song_added(entry)

    def remove_song(self, song_id: str) -> None:
        removed_entry = None
        new_entries: List[PlaylistEntry] = []
        for entry in self.entries:
            if entry.song_id == song_id and removed_entry is None:
                removed_entry = entry
                continue
            new_entries.append(entry)
        self.entries = new_entries
        if removed_entry and self.song_removed:
            self.song_removed(removed_entry)

    def get_song_ids(self) -> List[str]:
        return [entry.song_id for entry in self.entries]

    def get_entries(self) -> List[PlaylistEntry]:
        return self.entries

    def get_songs_metadata(self, song_library: SongLibrary) -> List[PlaylistEntry]:
        songs: List[PlaylistEntry] = []
        to_remove: List[str] = []
        for entry in self.entries:
            song = song_library.get_song(entry.song_id)
            if song is not None:
                logger.info(f"Found song: {entry.song_id}")
                songs.append(entry)
            else:
                logger.warning(
                    f"Song not found: {entry.song_id}, removing from playlist"
                )
                to_remove.append(entry.song_id)
        for song_id in to_remove:
            self.remove_song(song_id)
        return songs

    @staticmethod
    def load_playlist(file_path: str) -> Optional["Playlist"]:
        try:
            with open(file_path, "r") as f:
                playlist_data = json.load(f)
                logger.info(f"Loaded playlist: {playlist_data['name']}")
                entries = [
                    PlaylistEntry.from_dict(e) for e in playlist_data.get("entries", [])
                ]
                # fallback for old format
                if not entries and "song_ids" in playlist_data:
                    entries = [
                        PlaylistEntry(song_id) for song_id in playlist_data["song_ids"]
                    ]
                return Playlist(
                    id=playlist_data["id"],
                    name=playlist_data["name"],
                    entries=entries,
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
                        "entries": [entry.to_dict() for entry in playlist.entries],
                    },
                    f,
                    indent=4,
                )
            logger.info(f"Playlist saved to {file_path}")
        except IOError as e:
            logger.error(f"Failed to save playlist to {file_path}: {e}")

    def set_song_order(self, order: List[int]) -> None:
        if len(order) != len(self.entries):
            logger.error("Order length does not match number of songs in playlist.")
            return
        try:
            self.entries = [self.entries[i] for i in order]
            logger.info(
                f"Playlist order updated: {[entry.song_id for entry in self.entries]}"
            )
        except IndexError as e:
            logger.error(f"Invalid index in order list: {e}")

    def get_song_id_by_index(self, index: int) -> Optional[str]:
        if 0 <= index < len(self.entries):
            return self.entries[index].song_id
        logger.warning(f"Index out of range: {index}")
        return None
