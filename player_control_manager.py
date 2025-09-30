from enum import Enum, auto

from loguru import logger
from main_window import MainWindow  # type: ignore
from player_thread import PlayerThread  # type: ignore
from playlist.playlist import Playlist  # type: ignore
from queue_manager import QueueManager  # type: ignore


class PlayerControlManager:
    class PlayerState(Enum):
        STOPPED = auto()
        PLAYING = auto()
        PAUSED = auto()

    def __init__(self, main_window: "MainWindow") -> None:
        self.main_window = main_window
        self.player_backend = main_window.player_backends["FakeBackend"]()
        self.state = self.PlayerState.STOPPED
        self.player_thread = None  # Changed: initialize as None
        self.queue_manager = QueueManager(history_playlist=Playlist(name="History"))

    def set_player_state(self, new_state: "PlayerControlManager.PlayerState") -> None:
        logger.debug(f"Player state changed from {self.state} to {new_state}")
        match (self.state, new_state):
            case (self.PlayerState.STOPPED, self.PlayerState.PLAYING):
                # Create a new thread instance each time we start from STOPPED
                self.player_thread = PlayerThread(
                    player_backend=self.player_backend,
                    audio_backend=self.main_window.audio_backend,
                    on_position_changed=self.on_position_changed,
                    on_song_finished=self.on_song_finished,
                )
                self.player_thread.start()
            case (self.PlayerState.PAUSED, self.PlayerState.PLAYING):
                if self.player_thread:
                    self.player_thread.pause()
            case (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
                if self.player_thread:
                    self.player_thread.pause()
            case (
                (self.PlayerState.PLAYING | self.PlayerState.PAUSED),
                self.PlayerState.STOPPED,
            ):
                if self.player_thread:
                    self.player_thread.stop()
                    self.player_thread.join()  # Ensure thread is cleaned up
                    self.player_thread = None
            case _:
                logger.warning(
                    f"Unhandled state transition from {self.state} to {new_state}"
                )
        self.state = new_state

    def on_play_pressed(self) -> None:
        self.set_player_state(self.PlayerState.PLAYING)

    def on_pause_pressed(self) -> None:
        self.set_player_state(self.PlayerState.PAUSED)

    def on_stop_pressed(self) -> None:
        self.set_player_state(self.PlayerState.STOPPED)

    def on_previous_pressed(self) -> None:
        if self.state in (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
            self.player_backend.previous()

    def on_next_pressed(self) -> None:
        if self.state in (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
            self.player_backend.next()

    def on_seek(self, position: int) -> None:
        if self.state in (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
            self.player_backend.seek(position)

    def on_volume_changed(self, value: int) -> None:
        if self.state in (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
            self.player_backend.set_volume(value)

    def on_position_changed(self, current_position: int, module_length: int) -> None:
        self.main_window.ui_manager.update_progress_bar(current_position, module_length)

    def on_song_finished(self) -> None:
        self.set_player_state(self.PlayerState.STOPPED)
        # Handle end of song, e.g., play next song in playlist
        pass

    def play_song_from_index(self, index: int, playlist: Playlist) -> None:
        song_id = playlist.get_song_id_by_index(index)
        if song_id is None:
            logger.error(f"No song found at index {index} in playlist {playlist.name}")
            return

        song = self.main_window.song_library.get_song(song_id)
        if song is None:
            logger.error(f"Song with ID {song_id} not found in song library")
            return

        self.player_backend.load_song(song)
        self.set_player_state(self.PlayerState.PLAYING)