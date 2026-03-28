from typing import Callable, Optional

from SettingsManager import SettingsManager

from PyRetroPlayer.player_backends.player_backend import PlayerBackend
from PyRetroPlayer.player_thread.base_player_thread_manager import (
    BasePlayerThreadManager,
)
from PyRetroPlayer.player_thread.recorder_player_thread import RecorderPlayerThread


class RecorderPlayerThreadManager(BasePlayerThreadManager):
    def __init__(
        self,
        settings_manager: SettingsManager,
        on_position_changed: Optional[Callable[[int, int], None]] = None,
        on_song_finished: Optional[Callable[[], None]] = None,
        filename: str = "",
    ) -> None:
        super().__init__(settings_manager, on_position_changed, on_song_finished)
        self.filename = filename

    def start(self, player_backend: PlayerBackend) -> None:
        self.player_thread = RecorderPlayerThread(
            player_backend=player_backend,
            settings_manager=self.settings_manager,
            events=self.events,
            filename=self.filename,
        )

        self.player_thread.start()

    def is_active(self) -> bool:
        return self.player_thread is not None
