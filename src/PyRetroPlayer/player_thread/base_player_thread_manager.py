from typing import Callable, Optional

from SettingsManager import SettingsManager

from PyRetroPlayer.player_backends.player_backend import PlayerBackend
from PyRetroPlayer.player_events import PlayerEvents
from PyRetroPlayer.player_thread.base_player_thread import BasePlayerThread


class BasePlayerThreadManager:
    def __init__(
        self,
        settings_manager: SettingsManager,
        on_position_changed: Optional[Callable[[int, int], None]] = None,
        on_song_finished: Optional[Callable[[], None]] = None,
    ) -> None:

        self.player_thread: Optional[BasePlayerThread] = None
        self.settings_manager: SettingsManager = settings_manager

        self.events: PlayerEvents = PlayerEvents()

        # connect signals to UI callbacks
        if on_position_changed:
            self.events.position_changed.connect(on_position_changed)
        if on_song_finished:
            self.events.song_finished.connect(on_song_finished)

    def start(self, player_backend: PlayerBackend) -> None:
        if self.player_thread:
            self.player_thread.start()

    def stop(self) -> None:
        if self.player_thread:
            self.player_thread.stop()
            self.player_thread.join()
            self.player_thread = None

    def is_active(self) -> bool:
        return self.player_thread is not None
