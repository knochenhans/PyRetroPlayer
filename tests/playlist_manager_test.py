import json
import os
import uuid
from pathlib import Path
from typing import List

import pytest

from PyRetroPlayer.playlist.playlist import Playlist


class DummySong:
    def __init__(self, id: str, title: str) -> None:
        self.id = id
        self.title = title


class DummySongLibrary:
    def __init__(self, songs: List[DummySong]) -> None:
        self.songs = {song.id: song for song in songs}

    def get_song(self, song_id: str) -> DummySong:
        return self.songs.get(song_id)


@pytest.fixture
def playlist() -> Playlist:
    return Playlist(name="Test Playlist")


@pytest.fixture
def song_ids() -> List[str]:
    return [str(uuid.uuid4()) for _ in range(3)]


def test_add_song(playlist: Playlist, song_ids: List[str]) -> None:
    playlist.add_song(song_ids[0])
    assert playlist.get_songs() == [song_ids[0]]
    playlist.add_song(song_ids[0])  # Should not duplicate
    assert playlist.get_songs() == [song_ids[0]]


def test_remove_song(playlist: Playlist, song_ids: List[str]) -> None:
    playlist.add_song(song_ids[0])
    playlist.remove_song(song_ids[0])
    assert playlist.get_songs() == []


def test_get_songs(playlist: Playlist, song_ids: List[str]) -> None:
    for sid in song_ids:
        playlist.add_song(sid)
    assert playlist.get_songs() == song_ids


def test_get_songs_metadata_removes_missing(
    playlist: Playlist, song_ids: List[str]
) -> None:
    # Add two valid, one invalid
    valid_song = DummySong(song_ids[0], "Song 1")
    valid_song2 = DummySong(song_ids[1], "Song 2")
    library = DummySongLibrary([valid_song, valid_song2])
    playlist.song_ids = [song_ids[0], song_ids[1], "missing_id"]
    songs = playlist.get_songs_metadata(library)
    assert len(songs) == 2
    assert playlist.get_songs() == [song_ids[0], song_ids[1]]


def test_set_song_order(playlist: Playlist, song_ids: List[str]) -> None:
    playlist.song_ids = song_ids.copy()
    playlist.set_song_order([2, 0, 1])
    assert playlist.get_songs() == [song_ids[2], song_ids[0], song_ids[1]]


def test_set_song_order_invalid_length(
    playlist: Playlist, song_ids: List[str], caplog
) -> None:
    playlist.song_ids = song_ids.copy()
    playlist.set_song_order([0, 1])  # Should not change order
    assert playlist.get_songs() == song_ids


def test_set_song_order_invalid_index(
    playlist: Playlist, song_ids: List[str], caplog
) -> None:
    playlist.song_ids = song_ids.copy()
    playlist.set_song_order([0, 1, 99])  # Should not raise, but log error
    # The order should not be changed for invalid index
    assert playlist.get_songs() == song_ids


def test_save_and_load_playlist(tmp_path: Path, song_ids: List[str]) -> None:
    playlist = Playlist(name="Test", song_ids=song_ids)
    file_path = tmp_path / "playlist.json"
    Playlist.save_playlist(playlist, str(file_path))
    assert file_path.exists()
    loaded = Playlist.load_playlist(str(file_path))
    assert loaded is not None
    assert loaded.name == "Test"
    assert loaded.get_songs() == song_ids


def test_load_playlist_invalid_file(tmp_path: Path) -> None:
    file_path = tmp_path / "invalid.json"
    file_path.write_text("not a json")
    loaded = Playlist.load_playlist(str(file_path))
    assert loaded is None


def test_load_playlist_missing_file(tmp_path: Path) -> None:
    file_path = tmp_path / "missing.json"
    loaded = Playlist.load_playlist(str(file_path))
    assert loaded is None
