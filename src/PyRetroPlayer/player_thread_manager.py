from typing import Callable

from audio_backends.audio_backend import AudioBackend  # type: ignore
from player_backends.player_backend import PlayerBackend  # type: ignore
from player_thread import PlayerThread  # type: ignore


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
