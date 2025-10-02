from playlist.playlist_tree_view import PlaylistTreeView  # type: ignore
from main_window import MainWindow  # type: ignore
from typing import Callable, List, Tuple
from PySide6.QtGui import QAction, QIcon  # type: ignore


class ActionsManager:
    actions_data: List[
        Tuple[str, str, str, str, Callable[[MainWindow], Callable[[], None]]]
    ] = [
        (
            "stop",
            "media-playback-stop",
            "Stop",
            "Stop playback",
            lambda main_window: main_window.player_control_manager.on_stop_pressed,
        ),
        (
            "play",
            "media-playback-start",
            "Play",
            "Start playback",
            lambda main_window: main_window.player_control_manager.on_play_pressed,
        ),
        (
            "pause",
            "media-playback-pause",
            "Pause",
            "Pause playback",
            lambda main_window: main_window.player_control_manager.on_pause_pressed,
        ),
        (
            "previous",
            "media-skip-backward",
            "Previous",
            "Previous track",
            lambda main_window: main_window.player_control_manager.on_previous_pressed,
        ),
        (
            "next",
            "media-skip-forward",
            "Next",
            "Next track",
            lambda main_window: main_window.player_control_manager.on_next_pressed,
        ),
        (
            "song_info_dialog",
            "dialog-information",
            "Song Information",
            "Show information about the current song",
            lambda main_window: main_window.playlist_ui_manager.current_tree_view.on_song_info_dialog,
        ),
    ]

    @staticmethod
    def create_actions(
        main_window: MainWindow,
        playlist_tree_view: PlaylistTreeView,
    ) -> List[QAction]:
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
            action.triggered.connect(slot_method_factory(main_window))
            actions.append(action)
        return actions

    @staticmethod
    def get_actions_by_names(
        main_window: MainWindow, action_names: List[str]
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
                action.triggered.connect(slot_method_factory(main_window))
                actions.append(action)
        return actions
