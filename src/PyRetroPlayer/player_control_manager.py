from enum import Enum, auto

from loguru import logger
from main_window import MainWindow  # type: ignore
from player_thread_manager import PlayerThreadManager  # type: ignore
from queue_manager import QueueManager  # type: ignore

from playlist.playlist import Playlist  # type: ignore


class PlayerControlManager:
    class PlayerState(Enum):
        STOPPED = auto()
        PLAYING = auto()
        PAUSED = auto()

    def __init__(self, main_window: "MainWindow") -> None:
        self.main_window = main_window
        self.state = self.PlayerState.STOPPED
        self.player_thread_manager = PlayerThreadManager(
            audio_backend=self.main_window.audio_backend,
            on_position_changed=self.on_position_changed,
            on_song_finished=self.on_song_finished,
        )
        self.history_playlist = Playlist(name="History")
        self.queue_manager = QueueManager(self.history_playlist)
        self.current_playlist = None
        self.current_playlist_index = -1
        self.current_backend = None

    def set_player_state(self, new_state: "PlayerControlManager.PlayerState") -> None:
        logger.debug(f"Player state changed from {self.state} to {new_state}")
        match (self.state, new_state):
            case (self.PlayerState.STOPPED, self.PlayerState.PLAYING):
                next_entry = self.queue_manager.pop_next_entry()

                if not next_entry and self.current_playlist:
                    num_entries = self.add_more_songs_to_queue(
                        self.current_playlist, self.current_playlist_index
                    )

                    if num_entries == 0:
                        logger.info(
                            "No more songs to add to the queue, stopping playback."
                        )
                        return

                song = self.main_window.song_library.get_song(
                    next_entry.song_id if next_entry else ""
                )
                if song:
                    backend_name = song.available_backends[0]
                    backend_factory = self.main_window.player_backends.get(backend_name)
                    if backend_factory:
                        self.current_backend = backend_factory()
                    else:
                        self.current_backend = None

                    if self.current_backend:
                        self.current_backend.load_song(song)
                        self.player_thread_manager.start(self.current_backend)
                        if next_entry:
                            self.history_playlist.add_entry(next_entry)
                        if self.current_playlist:
                            self.current_playlist.set_currently_playing_entry(
                                next_entry if next_entry else None
                            )
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

    def on_play_pressed(self) -> None:
        self.set_player_state(self.PlayerState.PLAYING)

    def on_pause_pressed(self) -> None:
        self.set_player_state(self.PlayerState.PAUSED)

    def on_stop_pressed(self) -> None:
        self.set_player_state(self.PlayerState.STOPPED)

    def on_previous_pressed(self) -> None:
        if self.state in (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
            if self.current_backend:
                self.current_backend.previous()

    def on_next_pressed(self) -> None:
        if self.state in (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
            if self.current_backend:
                self.current_backend.next()

    def on_seek(self, position: int) -> None:
        if self.state in (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
            if self.current_backend:
                self.current_backend.seek(position)

    def on_volume_changed(self, value: int) -> None:
        if self.state in (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
            if self.current_backend:
                self.current_backend.set_volume(value)

    def on_position_changed(self, current_position: int, module_length: int) -> None:
        self.main_window.ui_manager.update_progress_bar(current_position, module_length)

    def on_song_finished(self) -> None:
        self.set_player_state(self.PlayerState.STOPPED)
        self.play_next()

    def play_next(self) -> None:
        self.play_queue()

    def play_queue(self) -> None:
        self.set_player_state(self.PlayerState.PLAYING)
        # song = self.queue_manager.pop_next_song()

        # if song:
        #     pass
        # else:
        #     if PlayingMode.RANDOM:
        #         self.populate_queue()
        #         song = self.queue_manager.pop_next_song()

        #         if song:
        #             self.play_module(song)

    def play_song_from_index(self, start_index: int, playlist: Playlist) -> None:
        self.current_playlist = playlist
        self.current_playlist_index = start_index
        self.add_more_songs_to_queue(playlist, start_index)
        self.set_player_state(self.PlayerState.PLAYING)

    def add_more_songs_to_queue(
        self, playlist: Playlist, start_index: int, count: int = 10
    ) -> int:
        entries = playlist.get_entries_from_index(start_index, count)
        self.queue_manager.add_entries(entries)
        self.current_playlist_index += len(entries)
        return len(entries)
