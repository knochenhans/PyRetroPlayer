import os
from typing import List

from appdirs import user_data_dir  # type: ignore
from loguru import logger
from playlist.playlist import Playlist  # type: ignore


class PlaylistManager:
    def __init__(self, app_name: str) -> None:
        self.app_name = app_name
        self.playlists_path = os.path.join(user_data_dir(self.app_name), "playlist")  # type: ignore
        os.makedirs(self.playlists_path, exist_ok=True)
        self.playlists: List[Playlist] = []

    def add_playlist(self, playlist: Playlist) -> None:
        self.playlists.append(playlist)
        logger.info(f"Added playlist: {playlist.name}")

    def delete_playlist(self, index: int) -> None:
        if 0 <= index < len(self.playlists):
            playlist_name = self.playlists[index].name
            del self.playlists[index]
            logger.info(f"Deleted playlist: {playlist_name}")
        else:
            logger.warning("Invalid playlist index to delete.")

    def load_playlists(self) -> None:
        self.playlists.clear()
        for filename in sorted(os.listdir(self.playlists_path)):
            if filename.endswith(".json"):
                playlist_file_path = os.path.join(self.playlists_path, filename)
                playlist = Playlist.load_playlist(playlist_file_path)
                if playlist:
                    self.playlists.append(playlist)

    def save_playlists(self) -> None:
        # Remove existing files in the playlists directory
        for filename in os.listdir(self.playlists_path):
            file_path = os.path.join(self.playlists_path, filename)
            if os.path.isfile(file_path) and filename.endswith(".json"):
                os.remove(file_path)

        # Save current playlists
        for i, playlist in enumerate(self.playlists):
            playlist_file_path = os.path.join(self.playlists_path, f"{i}.json")
            Playlist.save_playlist(playlist, playlist_file_path)

    def reorder_playlists(self, from_index: int, to_index: int) -> None:
        if 0 <= from_index < len(self.playlists) and 0 <= to_index < len(
            self.playlists
        ):
            playlist = self.playlists.pop(from_index)
            self.playlists.insert(to_index, playlist)
            logger.info(f"Reordered playlists: {from_index} -> {to_index}")
        else:
            logger.warning("Invalid indices for playlist reordering.")
