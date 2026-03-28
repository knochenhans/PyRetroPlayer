from typing import Callable, Optional

from SettingsManager import SettingsManager

from PyRetroPlayer.audio_backends.audio_backend import AudioBackend
from PyRetroPlayer.player_backends.player_backend import PlayerBackend
from PyRetroPlayer.player_thread.base_player_thread_manager import (
    BasePlayerThreadManager,
)
from PyRetroPlayer.player_thread.player_thread import PlayerThread


class PlayerThreadManager(BasePlayerThreadManager):
    def __init__(
        self,
        audio_backend: AudioBackend,
        settings_manager: SettingsManager,
        on_position_changed: Optional[Callable[[int, int], None]] = None,
        on_song_finished: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(
            settings_manager=settings_manager,
            on_position_changed=on_position_changed,
            on_song_finished=on_song_finished,
        )

        self.audio_backend: AudioBackend = audio_backend

    def start(self, player_backend: PlayerBackend) -> None:
        self.player_thread = PlayerThread(
            player_backend=player_backend,
            audio_backend=self.audio_backend,
            settings_manager=self.settings_manager,
            events=self.events,
        )

        self.player_thread.start()

    def pause(self) -> None:
        if self.player_thread and isinstance(self.player_thread, PlayerThread):
            self.player_thread.pause()

    def is_active(self) -> bool:
        return self.player_thread is not None
