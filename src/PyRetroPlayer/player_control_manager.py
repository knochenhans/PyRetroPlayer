from enum import Enum, auto
from typing import Callable, List

from audio_backends.audio_backend import AudioBackend  # type: ignore
from loguru import logger
from main_window import MainWindow  # type: ignore
from player_backends.player_backend import PlayerBackend  # type: ignore
from player_thread import PlayerThread  # type: ignore
from queue_manager import QueueManager  # type: ignore

from playlist.playlist import Playlist  # type: ignore
from playlist.song import Song  # type: ignore


class PlayerThreadManager:
    def __init__(
        self,
        player_backend: "PlayerBackend",
        audio_backend: "AudioBackend",
        on_position_changed: Callable[[int, int], None],
        on_song_finished: Callable[[], None],
    ):
        self.player_thread = None
        self.player_backend = player_backend
        self.audio_backend = audio_backend
        self.on_position_changed = on_position_changed
        self.on_song_finished = on_song_finished
        self.on_song_finished = on_song_finished

    def start(self):
        self.player_thread = PlayerThread(
            player_backend=self.player_backend,
            audio_backend=self.audio_backend,
            on_position_changed=self.on_position_changed,
            on_song_finished=self.on_song_finished,
        )
        self.player_thread.start()

    def pause(self):
        if self.player_thread:
            self.player_thread.pause()

    def stop(self):
        if self.player_thread:
            self.player_thread.stop()
            self.player_thread = None

    def is_active(self):
        return self.player_thread is not None


class PlayerControlManager:
    class PlayerState(Enum):
        STOPPED = auto()
        PLAYING = auto()
        PAUSED = auto()

    def __init__(self, main_window: "MainWindow") -> None:
        self.main_window = main_window
        self.player_backend = main_window.player_backends["FakeBackend"]()
        self.state = self.PlayerState.STOPPED
        self.player_thread_manager = PlayerThreadManager(
            player_backend=self.player_backend,
            audio_backend=self.main_window.audio_backend,
            on_position_changed=self.on_position_changed,
            on_song_finished=self.on_song_finished,
        )
        self.history_playlist = Playlist(name="History")
        self.queue_manager = QueueManager(self.history_playlist)

    def set_player_state(self, new_state: "PlayerControlManager.PlayerState") -> None:
        logger.debug(f"Player state changed from {self.state} to {new_state}")
        match (self.state, new_state):
            case (self.PlayerState.STOPPED, self.PlayerState.PLAYING):
                self.player_backend.load_song(self.queue_manager.pop_next_song())
                self.player_thread_manager.start()
            case (self.PlayerState.PAUSED, self.PlayerState.PLAYING):
                self.player_thread_manager.pause()
            case (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
                self.player_thread_manager.pause()
            case (
                (self.PlayerState.PLAYING | self.PlayerState.PAUSED),
                self.PlayerState.STOPPED,
            ):
                self.player_thread_manager.stop()
            case _:
                logger.warning(
                    f"Unhandled state transition from {self.state} to {new_state}"
                )
        self.state = new_state

        # if new_state == self.PlayerState.PLAYING:
        #     self.main_window.playlist_ui_manager.

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
        self.play_next()

    def play_next(self) -> None:
        self.play_queue()

    def play_queue(self) -> None:
        song = self.queue_manager.pop_next_song()

        if song:
            # self.play_song_from_index(song)
            pass
        # else:
        #     if PlayingMode.RANDOM:
        #         self.populate_queue()
        #         song = self.queue_manager.pop_next_song()

        #         if song:
        #             self.play_module(song)

    def play_song_from_index(self, index: int, playlist: Playlist) -> None:
        entries = playlist.get_entries_from_index(index, 10)

        songs: List[Song] = self.main_window.song_library.get_songs(
            [entry.song_id for entry in entries]
        )

        self.queue_manager.add_songs(songs)
        self.set_player_state(self.PlayerState.PLAYING)
