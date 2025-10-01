import os
import tempfile
import typing
import uuid

import pytest

from PyRetroPlayer.playlist.song import Song
from PyRetroPlayer.playlist.song_library import SongLibrary


@pytest.fixture
def temp_db() -> typing.Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name
    try:
        yield db_path
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.fixture
def sample_song() -> Song:
    return Song(
        id=str(uuid.uuid4()),
        file_path="test_song.mp3",
        title="Test Song",
        artist="Test Artist",
        duration=123,
        available_backends=["local"],
        md5="md5hash",
        sha1="sha1hash",
        custom_metadata={"genre": "rock"},
    )


def test_add_and_get_song(temp_db: str, sample_song: Song) -> None:
    lib = SongLibrary(temp_db)
    lib.add_song(sample_song)
    fetched = lib.get_song(sample_song.id)
    assert fetched is not None
    assert fetched.title == sample_song.title
    assert fetched.artist == sample_song.artist
    assert fetched.custom_metadata["genre"] == "rock"
    lib.close()


def test_add_duplicate_song(temp_db: str, sample_song: Song) -> None:
    lib = SongLibrary(temp_db)
    lib.add_song(sample_song)
    lib.add_song(sample_song)  # Should not add duplicate
    songs = lib.get_all_songs()
    assert len(songs) == 1
    lib.close()


def test_remove_song(temp_db: str, sample_song: Song) -> None:
    lib = SongLibrary(temp_db)
    lib.add_song(sample_song)
    lib.remove_song(sample_song.id)
    assert lib.get_song(sample_song.id) is None
    lib.close()


def test_get_all_songs(temp_db: str, sample_song: Song) -> None:
    lib = SongLibrary(temp_db)
    lib.add_song(sample_song)
    another_song = Song(
        id=str(uuid.uuid4()),
        file_path="another.mp3",
        title="Another Song",
        artist="Another Artist",
        duration=321,
        available_backends=["local"],
        md5="md5hash2",
        sha1="sha1hash2",
        custom_metadata={},
    )
    lib.add_song(another_song)
    songs = lib.get_all_songs()
    titles = [s.title for s in songs]
    assert "Test Song" in titles
    assert "Another Song" in titles
    lib.close()


def test_check_song_exists(temp_db: str, sample_song: Song) -> None:
    lib = SongLibrary(temp_db)
    lib.add_song(sample_song)
    assert lib.check_song_exists(sample_song.id)
    assert not lib.check_song_exists("nonexistent_id")
    lib.close()


def test_remove_missing_files(temp_db: str, sample_song: Song) -> None:
    lib = SongLibrary(temp_db)
    # Add a song with a non-existent file path
    missing_song = Song(
        id=str(uuid.uuid4()),
        file_path="missing_file.mp3",
        title="Missing",
        artist="Nobody",
        duration=1,
        available_backends=["local"],
        md5="md5missing",
        sha1="sha1missing",
        custom_metadata={},
    )
    lib.add_song(missing_song)
    lib.remove_missing_files()
    assert not lib.check_song_exists(missing_song.id)
    lib.close()


def test_clear_library(temp_db: str, sample_song: Song) -> None:
    lib = SongLibrary(temp_db)
    lib.add_song(sample_song)
    lib.clear()
    assert lib.get_all_songs() == []
    lib.close()


def test_context_manager(temp_db: str, sample_song: Song) -> None:
    with SongLibrary(temp_db) as lib:
        lib.add_song(sample_song)
        assert lib.get_song(sample_song.id) is not None
