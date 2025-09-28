import os
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from appdirs import user_config_dir, user_data_dir  # type: ignore
from player_backends.fake_player_backend import FakePlayerBackend  # type: ignore
from playlist.playlist import Playlist  # type: ignore
from playlist.song import Song  # type: ignore
from playlist.song_library import SongLibrary  # type: ignore
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QIcon  # type: ignore
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSlider,
    QToolBar,
)


class MainWindow(QMainWindow):
    progress_bar_value_changed = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        self.application_name: str = "PyRetroPlayer"
        self.application_version: str = "0.1.0"

        self.config_dir = os.path.join(user_config_dir(), self.application_name)  # type: ignore
        os.makedirs(self.config_dir, exist_ok=True)

        self.data_dir = os.path.join(user_data_dir(), self.application_name)  # type: ignore
        os.makedirs(self.data_dir, exist_ok=True)

        self.setWindowTitle(f"{self.application_name} v{self.application_version}")

        self.song_library = SongLibrary(os.path.join(self.data_dir, "song_library.db"))

        from ui_manager import UIManager  # type: ignore

        self.ui_manager = UIManager(self)

        from file_manager import FileManager  # type: ignore

        self.file_manager = FileManager(self)

        from playlist_ui_manager import PlaylistUIManager  # type: ignore

        self.playlist_ui_manager = PlaylistUIManager(self)

        self.ui_manager.create_menu_bar()

        self.player_backends: Dict[str, Any] = {
            "FakeBackend": lambda: FakePlayerBackend()
        }

        from player_control_manager import PlayerControlManager  # type: ignore

        self.player_control_manager = PlayerControlManager(self)

        self.icon_bar = QToolBar("Main Toolbar", self)
        self.addToolBar(self.icon_bar)
        self.setup_icon_bar()

    def setup_icon_bar(self) -> None:
        icon_actions: List[Tuple[str, str, str, Callable[[], None]]] = [
            (
                "media-playback-stop",
                "Stop",
                "Stop playback",
                self.player_control_manager.on_stop_pressed,
            ),
            (
                "media-playback-start",
                "Play",
                "Start playback",
                self.player_control_manager.on_play_pressed,
            ),
            (
                "media-playback-pause",
                "Pause",
                "Pause playback",
                self.player_control_manager.on_pause_pressed,
            ),
            (
                "media-skip-backward",
                "Previous",
                "Previous track",
                self.player_control_manager.on_previous_pressed,
            ),
            (
                "media-skip-forward",
                "Next",
                "Next track",
                self.player_control_manager.on_next_pressed,
            ),
        ]

        for icon_name, action_text, status_tip, slot_method in icon_actions:
            icon = QIcon.fromTheme(icon_name)
            action = QAction(icon, action_text, self)
            action.setStatusTip(status_tip)
            action.triggered.connect(slot_method)
            self.icon_bar.addAction(action)

        self.icon_bar.addSeparator()

        # Add volume slider
        progress_slider = QSlider(Qt.Orientation.Horizontal)
        progress_slider.setRange(0, 100)
        progress_slider.setValue(0)
        progress_slider.setToolTip("Playback Progress")
        # progress_slider.valueChanged.connect(self.on_progress_changed)
        self.icon_bar.addWidget(progress_slider)

        # progress_slider.sliderMoved.connect(self.on_seek)

        self.icon_bar.addSeparator()

        # Add progess slider
        volume_slider = QSlider(Qt.Orientation.Horizontal)
        volume_slider.setRange(0, 100)
        volume_slider.setValue(50)
        volume_slider.setToolTip("Volume")
        volume_slider.setMaximumWidth(100)

        # volume_slider.valueChanged.connect(self.on_volume_changed)
        self.icon_bar.addWidget(volume_slider)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.playlist_ui_manager.playlist_manager.save_playlists()
        self.playlist_ui_manager.tab_widget.update_tab_column_widths()
        self.save_column_managers()
        event.accept()

    def save_column_managers(self) -> None:
        columns_dir = os.path.join(
            self.playlist_ui_manager.playlist_manager.playlists_path, "columns"
        )
        os.makedirs(columns_dir, exist_ok=True)

        for (
            playlist_id,
            column_manager,
        ) in self.playlist_ui_manager.column_managers.items():
            config_path = os.path.join(columns_dir, f"{playlist_id}.json")
            column_manager.save_to_json(config_path)

    def remove_missing_files(self) -> None:
        self.song_library.remove_missing_files()

    def clear_song_library(self) -> None:
        self.song_library.clear()

    def load_all_songs_from_library(self) -> None:
        self.file_manager.load_all_songs_from_library()

    def load_files(self, file_paths: List[str], playlist: Playlist) -> None:
        self.file_manager.load_files(file_paths, playlist)

    def on_song_loaded(self, song: Optional[Song]) -> None:
        self.file_manager.on_song_loaded(song)

    def on_all_songs_loaded(self) -> None:
        self.file_manager.on_all_songs_loaded()


if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
