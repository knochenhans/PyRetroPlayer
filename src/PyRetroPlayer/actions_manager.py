from player_control_manager import PlayerControlManager  # type: ignore
from typing import Callable, List, Tuple
from PySide6.QtGui import QAction, QIcon  # type: ignore


class ActionsManager:
    actions_data: List[
        Tuple[str, str, str, str, Callable[[PlayerControlManager], Callable[[], None]]]
    ] = [
        (
            "stop",
            "media-playback-stop",
            "Stop",
            "Stop playback",
            lambda player_control_manager: player_control_manager.on_stop_pressed,
        ),
        (
            "play",
            "media-playback-start",
            "Play",
            "Start playback",
            lambda player_control_manager: player_control_manager.on_play_pressed,
        ),
        (
            "pause",
            "media-playback-pause",
            "Pause",
            "Pause playback",
            lambda player_control_manager: player_control_manager.on_pause_pressed,
        ),
        (
            "previous",
            "media-skip-backward",
            "Previous",
            "Previous track",
            lambda player_control_manager: player_control_manager.on_previous_pressed,
        ),
        (
            "next",
            "media-skip-forward",
            "Next",
            "Next track",
            lambda player_control_manager: player_control_manager.on_next_pressed,
        ),
    ]

    @staticmethod
    def create_actions(player_control_manager: PlayerControlManager) -> List[QAction]:
        actions: List[QAction] = []
        for (
            action_name,
            icon_name,
            action_text,
            status_tip,
            slot_method_factory,
        ) in ActionsManager.actions_data:
            action_name = action_name
            icon = QIcon.fromTheme(icon_name)
            action = QAction(icon, action_text)
            action.setStatusTip(status_tip)
            action.triggered.connect(slot_method_factory(player_control_manager))
            actions.append(action)
        return actions

    @staticmethod
    def get_actions_by_names(
        player_control_manager: PlayerControlManager, action_names: List[str]
    ) -> List[QAction]:
        actions: List[QAction] = []
        for (
            action_name,
            icon_name,
            action_text,
            status_tip,
            slot_method_factory,
        ) in ActionsManager.actions_data:
            if action_name in action_names:
                icon = QIcon.fromTheme(icon_name)
                action = QAction(icon, action_text)
                action.setStatusTip(status_tip)
                action.triggered.connect(slot_method_factory(player_control_manager))
                actions.append(action)
        return actions
