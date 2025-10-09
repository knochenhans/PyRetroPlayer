from enum import Enum, auto
from typing import Callable, Optional

from loguru import logger

from PyRetroPlayer.main_window import MainWindow
from PyRetroPlayer.player_thread_manager import PlayerThreadManager
from PyRetroPlayer.playlist.playlist import Playlist
from PyRetroPlayer.playlist.song import Song
from PyRetroPlayer.queue_manager import QueueManager
from PyRetroPlayer.settings.settings import Settings


class PlayerControlManager:
    class PlayerState(Enum):
        STOPPED = auto()
        PLAYING = auto()
        PAUSED = auto()

    def __init__(
        self,
        main_window: "MainWindow",
        settings: Settings,
        play_callback: Optional[Callable[[], None]] = None,
        pause_callback: Optional[Callable[[], None]] = None,
        stop_callback: Optional[Callable[[], None]] = None,
        previous_callback: Optional[Callable[[], None]] = None,
        next_callback: Optional[Callable[[], None]] = None,
        seek_callback: Optional[Callable[[int], None]] = None,
        volume_changed_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        self.main_window = main_window
        self.state = self.PlayerState.STOPPED
        self.player_thread_manager = PlayerThreadManager(
            audio_backend=self.main_window.audio_backend,
            settings=settings,
            on_position_changed=self.on_position_changed,
            on_song_finished=self.on_song_finished,
        )
        self.history_playlist = Playlist(name="History")
        self.queue_manager = QueueManager(self.history_playlist)
        self.current_playlist: Optional[Playlist] = None
        self.current_playlist_index = -1
        self.current_backend = None

        # Add callbacks for UI buttons
        self.play_callback = play_callback
        self.pause_callback = pause_callback
        self.stop_callback = stop_callback
        self.previous_callback = previous_callback
        self.next_callback = next_callback
        self.seek_callback = seek_callback
        self.volume_changed_callback = volume_changed_callback

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
                    self.on_current_song_changed(song)
                    self.play_song(song)

                if next_entry:
                    self.history_playlist.add_entry(next_entry)

                    if self.current_playlist:
                        self.current_playlist.set_currently_playing_entry(next_entry)
            case (
                self.PlayerState.PAUSED,
                self.PlayerState.PLAYING | self.PlayerState.PAUSED,
            ):
                self.player_thread_manager.pause()
            case (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
                self.player_thread_manager.pause()
            case (
                (self.PlayerState.PLAYING | self.PlayerState.PAUSED),
                self.PlayerState.STOPPED,
            ):
                self.player_thread_manager.stop()
            case (self.PlayerState.PLAYING, self.PlayerState.PLAYING):
                self.player_thread_manager.pause()
            case _:
                logger.warning(
                    f"Unhandled state transition from {self.state} to {new_state}"
                )
        self.state = new_state

        match self.state:
            case self.PlayerState.STOPPED:
                if self.stop_callback:
                    self.stop_callback()
            case self.PlayerState.PLAYING:
                if self.play_callback:
                    self.play_callback()
            case self.PlayerState.PAUSED:
                if self.pause_callback:
                    self.pause_callback()
            case _:
                pass

    def on_current_song_changed(self, song: Song) -> None:
        song_title = song.title
        if song_title == "":
            song_title = f"{song.file_path.split('/')[-1]}"
        if song.artist:
            song_title += f" - {song.artist}"
        self.main_window.tray_manager.show_tray_notification(
            "Now Playing", song_title
        )
        self.main_window.ui_manager.update_window_title(song_title)

        comments = song.custom_metadata.get("comments", [])

        for comment in comments:
            self.main_window.tray_manager.show_tray_notification(
                "Comment", comment
            )

    def play_song(self, song: Song) -> None:
        backend_name = song.available_backends[0]
        backend_factory = self.main_window.player_backends.get(backend_name)
        if backend_factory:
            self.current_backend = backend_factory()
        else:
            self.current_backend = None

        if self.current_backend:
            self.current_backend.load_song(song)
            self.player_thread_manager.start(self.current_backend)

    def on_play_pressed(self) -> None:
        self.set_player_state(self.PlayerState.PLAYING)

    def on_pause_pressed(self) -> None:
        if self.state == self.PlayerState.PLAYING:
            self.set_player_state(self.PlayerState.PAUSED)
        else:
            self.set_player_state(self.PlayerState.PLAYING)

    def on_stop_pressed(self) -> None:
        self.set_player_state(self.PlayerState.STOPPED)

    def on_previous_pressed(self) -> None:
        if self.state in (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
            if self.current_backend:
                self.current_backend.previous()

    def on_next_pressed(self) -> None:
        if self.state in (self.PlayerState.PLAYING, self.PlayerState.PAUSED):
            self.play_next()

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
        self.set_player_state(self.PlayerState.STOPPED)
        self.play_queue()

    def play_queue(self) -> None:
        if self.queue_manager.is_empty():
            if self.current_playlist:
                num_entries = self.add_more_songs_to_queue(
                    self.current_playlist, self.current_playlist_index
                )

                if num_entries == 0:
                    logger.info("No more songs to add to the queue, stopping playback.")
                    self.set_player_state(self.PlayerState.STOPPED)
                    return
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
        self.set_player_state(self.PlayerState.STOPPED)
        self.current_playlist = playlist
        self.current_playlist_index = start_index
        self.queue_manager.clear()
        self.add_more_songs_to_queue(playlist, start_index)
        self.play_queue()

    def add_more_songs_to_queue(
        self, playlist: Playlist, start_index: int, count: int = 10
    ) -> int:
        entries = playlist.get_entries_from_index(start_index, count)
        self.queue_manager.add_entries(entries)
        self.current_playlist_index += len(entries)
        return len(entries)
