from typing import Callable, List, Tuple

from PySide6.QtGui import QAction, QIcon

from PyRetroPlayer.main_window import MainWindow


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
            lambda main_window: main_window.playlist_ui_manager.show_song_info_dialog,
        ),
        (
            "get_random_module",
            "system-search",
            "Get Random Module",
            "Fetch and play a random module from the web",
            lambda main_window: main_window.file_manager.get_random_module,
        ),
        (
            "lookup_modarchive",
            "system-search",
            "Lookup on ModArchive",
            "Lookup current song on ModArchive",
            lambda main_window: main_window.on_lookup_modarchive,
        ),
        (
            "lookup_msm",
            "system-search",
            "Lookup on .mod Sample Master",
            "Lookup current song on .mod Sample Master",
            lambda main_window: main_window.on_lookup_msm,
        ),
        (
            "download_favorites",
            "folder-download",
            "Download Favorites",
            "Download favorite modules of the current member",
            lambda main_window: main_window.download_favorite_modules,
        ),
    ]

    @staticmethod
    def create_actions(main_window: MainWindow) -> List[QAction]:
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
