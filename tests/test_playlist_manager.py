import os
from unittest.mock import mock_open, patch

import pytest

from playlist.playlist import Playlist
from playlist.playlist_manager import PlaylistManager


@pytest.fixture
def setup_manager():
    app_name = "TestApp"
    manager = PlaylistManager(app_name)
    test_playlist = Playlist(
        id="1", name="Test Playlist", items=[{"title": "song1"}, {"title": "song2"}]
    )
    return manager, test_playlist


@patch("os.makedirs")
@patch("playlist.playlist_manager.user_data_dir")
def test_init_creates_playlists_directory(mock_user_data_dir, mock_makedirs):
    app_name = "TestApp"
    mock_user_data_dir.return_value = "/mock/user/data/dir"
    manager = PlaylistManager(app_name)
    expected_path = os.path.join("/mock/user/data/dir", "playlist")
    mock_makedirs.assert_called_once_with(expected_path, exist_ok=True)


def test_add_playlist(setup_manager):
    manager, test_playlist = setup_manager
    manager.add_playlist(test_playlist)
    assert test_playlist in manager.playlists


def test_delete_playlist_valid_index(setup_manager):
    manager, test_playlist = setup_manager
    manager.add_playlist(test_playlist)
    manager.delete_playlist(0)
    assert test_playlist not in manager.playlists


@patch("os.listdir")
@patch("playlist.playlist_manager.PlaylistManager.load_playlist")
def test_load_playlists(mock_load_playlist, mock_listdir, setup_manager):
    manager, test_playlist = setup_manager
    mock_listdir.return_value = ["0.json", "1.json"]
    mock_load_playlist.side_effect = [test_playlist, None]
    manager.load_playlists()
    assert test_playlist in manager.playlists
    assert len(manager.playlists) == 1


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data='{"id": 1, "name": "Test Playlist", "data": ["song1", "song2"]}',
)
def test_load_playlist_valid_file(mock_open, setup_manager):
    manager, _ = setup_manager
    playlist = manager.load_playlist("mock_file.json")
    assert playlist is not None
    assert playlist.name == "Test Playlist"


@patch("builtins.open", side_effect=FileNotFoundError)
def test_load_playlist_file_not_found(mock_open, setup_manager):
    manager, _ = setup_manager
    playlist = manager.load_playlist("mock_file.json")
    assert playlist is None


@patch("builtins.open", new_callable=mock_open)
def test_save_playlist(mock_open, setup_manager):
    manager, test_playlist = setup_manager
    manager.save_playlist(test_playlist, "mock_file.json")
    mock_open.assert_called_once_with("mock_file.json", "w")
    handle = mock_open()
    handle.write.assert_called()


def test_reorder_playlists_valid_indices(setup_manager):
    manager, test_playlist = setup_manager
    playlist2 = Playlist(id="2", name="Another Playlist", items=[{"title": "song3"}])
    manager.add_playlist(test_playlist)
    manager.add_playlist(playlist2)
    manager.reorder_playlists(0, 1)
    assert manager.playlists[0] == playlist2
    assert manager.playlists[1] == test_playlist
