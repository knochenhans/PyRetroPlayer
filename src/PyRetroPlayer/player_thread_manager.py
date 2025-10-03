from typing import Callable, Optional

from PyRetroPlayer.audio_backends.audio_backend import AudioBackend
from PyRetroPlayer.player_backends.player_backend import PlayerBackend
from PyRetroPlayer.player_thread import PlayerThread
from PyRetroPlayer.settings.settings import Settings


class PlayerThreadManager:
    def __init__(
        self,
        audio_backend: AudioBackend,
        settings: Settings,
        on_position_changed: Callable[[int, int], None],
        on_song_finished: Callable[[], None],
    ):
        self.player_thread: Optional[PlayerThread] = None
        self.audio_backend = audio_backend
        self.settings = settings
        self.on_position_changed = on_position_changed
        self.on_song_finished = on_song_finished
        self.on_song_finished = on_song_finished

    def start(self, player_backend: PlayerBackend):
        self.player_thread = PlayerThread(
            player_backend=player_backend,
            audio_backend=self.audio_backend,
            settings=self.settings,
            on_position_changed=self.on_position_changed,
            on_song_finished=self.on_song_finished,
        )
        if self.player_thread:
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
