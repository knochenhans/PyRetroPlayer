from collections import deque
from typing import List, Optional

from loguru import logger

from PyRetroPlayer.playlist.playlist import Playlist
from PyRetroPlayer.playlist.playlist_entry import PlaylistEntry


class QueueManager:
    def __init__(self, history_playlist: Playlist) -> None:
        self.queue: deque[PlaylistEntry] = deque()
        self.history_playlist = history_playlist

        # Set current song index to -1 to indicate that no song is playing
        self.history_playlist.current_song_index = -1

    def add_entry(self, entry: PlaylistEntry) -> None:
        self.queue.append(entry)

    def add_entries(self, entries: List[PlaylistEntry]) -> None:
        self.queue.extend(entries)

    def set_queue(self, entries: List[PlaylistEntry]) -> None:
        self.queue = deque(entries)

    def update_entry(self, entry: PlaylistEntry) -> None:
        for idx, e in enumerate(self.queue):
            if e.entry_id == entry.entry_id:
                self.queue[idx] = entry
                break

    def pop_next_entry(self) -> Optional[PlaylistEntry]:
        if self.queue:
            entry = self.queue.popleft()

            # Add entry to history playlist
            self.history_playlist.entries.append(entry)
            self.history_playlist.current_song_index += 1

            if len(self.queue) > 0:
                logger.debug(
                    f'Playing "{entry.song_id}" from queue, remaining: {len(self.queue)}'
                )
            else:
                logger.debug("Queue is empty.")
            return entry
        return None

    def peek_next_entry(self) -> Optional[PlaylistEntry]:
        return self.queue[0] if self.queue else None

    def prioritize_entry(self, entry: PlaylistEntry) -> None:
        for e in self.queue:
            if e.entry_id == entry.entry_id:
                self.queue.remove(e)
                self.queue.appendleft(e)
                break

    def clear(self) -> None:
        self.queue.clear()

    def get_queue(self) -> List[PlaylistEntry]:
        return list(self.queue)

    def is_empty(self) -> bool:
        return not bool(self.queue)
