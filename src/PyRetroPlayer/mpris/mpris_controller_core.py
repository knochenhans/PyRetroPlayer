class MPRISControllerCore:
    player_control_manager: "PlayerControlManager"

    def __init__(self, player_control_manager: "PlayerControlManager") -> None:
        self.player_control_manager = player_control_manager
        self.playing: bool = False

    def play(self) -> None:
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
