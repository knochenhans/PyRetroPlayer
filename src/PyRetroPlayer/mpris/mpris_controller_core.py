import time


class MPRISControllerCore:
    player_control_manager: "PlayerControlManager"

    def __init__(self, player_control_manager: "PlayerControlManager") -> None:
        self.player_control_manager = player_control_manager
        self.playing: bool = False
        self.has_media: bool = False
        self._last_pause_time: float = 0.0

    def request_play(self) -> None:
        self.has_media = True
        self.playing = True
        self.player_control_manager.on_play_pressed()

    def external_play(self) -> None:
        if time.time() - self._last_pause_time < 1.0:
            return  # ignore resume glitch

        if not self.has_media:
            return

        self.playing = True
        self.player_control_manager.on_play_pressed()

    def pause(self) -> None:
        self.playing = False
        self.player_control_manager.on_pause_pressed()

    def toggle(self) -> None:
        self.playing = not self.playing
        if self.playing:
            self.player_control_manager.on_play_pressed()
        else:
            self.player_control_manager.on_pause_pressed()

    def next(self) -> None:
        self.player_control_manager.on_next_pressed()

    def previous(self) -> None:
        self.player_control_manager.on_previous_pressed()

    def stop(self) -> None:
        self.playing = False
        self.has_media = False
        self._last_pause_time = time.time()
        self.player_control_manager.on_stop_pressed()
