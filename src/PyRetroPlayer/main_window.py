import os
import sys
from typing import Any, Dict, List, Optional

from appdirs import user_config_dir, user_data_dir
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSlider,
    QToolBar,
)

from PyRetroPlayer.audio_backends.pyaudio.audio_backend_pyuadio import (
    AudioBackendPyAudio,
)
from PyRetroPlayer.player_backends.libopenmpt.player_backend_libopenmpt import (
    PlayerBackendLibOpenMPT,
)
from PyRetroPlayer.player_backends.libuade.player_backend_libuade import (
    PlayerBackendLibUADE,
)
from PyRetroPlayer.playlist.playlist import Playlist
from PyRetroPlayer.playlist.song import Song
from PyRetroPlayer.playlist.song_library import SongLibrary
from PyRetroPlayer.settings.settings import Settings


class MainWindow(QMainWindow):
    progress_bar_value_changed = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        self.application_name: str = "PyRetroPlayer"
        self.application_version: str = "0.1.0"

        self.config_dir = os.path.join(user_config_dir(), self.application_name)
        os.makedirs(self.config_dir, exist_ok=True)

        self.data_dir = os.path.join(user_data_dir(), self.application_name)
        os.makedirs(self.data_dir, exist_ok=True)

        self.settings: Settings = Settings(
            "configuration",
            self.config_dir,
            self.application_name,
        )
        self.settings.ensure_default_config()
        self.settings.load()

        # self.actions_: List[QAction] = []

        self.setWindowTitle(f"{self.application_name} v{self.application_version}")

        self.song_library = SongLibrary(os.path.join(self.data_dir, "song_library.db"))

        self.player_backends: Dict[str, Any] = {
            "LibUADE": lambda: PlayerBackendLibUADE(),
            # "FakeBackend": lambda: FakePlayerBackend(),
            "LibOpenMPT": lambda: PlayerBackendLibOpenMPT(),
        }
        self.player_backends_priorities: List[str] = [
            "LibUADE",
            "LibOpenMPT",
            # "FakeBackend",
        ]

        self.audio_backends: Dict[str, Any] = {"PyAudio": lambda: AudioBackendPyAudio()}
        self.audio_backend = self.audio_backends["PyAudio"]()

        from PyRetroPlayer.player_control_manager import PlayerControlManager

        self.player_control_manager = PlayerControlManager(self, self.settings)

        from PyRetroPlayer.file_manager import FileManager
        from PyRetroPlayer.playlist_ui_manager import PlaylistUIManager
        from PyRetroPlayer.ui_manager import UIManager

        self.ui_manager = UIManager(self)
        self.file_manager = FileManager(self)
        self.playlist_ui_manager = PlaylistUIManager(self)

        from PyRetroPlayer.actions_manager import ActionsManager

        self.actions_: List[QAction] = ActionsManager.get_actions_by_names(
            self, ["play", "pause", "stop", "previous", "next"]
        )

        self.playlist_ui_manager.setup_actions()

        self.ui_manager.create_menu_bar()

        self.icon_bar = QToolBar("Main Toolbar", self)
        self.addToolBar(self.icon_bar)

        self.setup_icon_bar()

        self.load_settings()

    def load_settings(self) -> None:
        geometry = self.settings.get("window_geometry")
        if geometry:
            try:
                x, y, w, h = geometry
                self.setGeometry(x, y, w, h)
            except Exception:
                pass

        self.playlist_ui_manager.tab_widget.setCurrentIndex(
            self.settings.get("last_active_playlist_index", 0)
        )

    def save_settings(self) -> None:
        geo = self.geometry()
        geometry = [geo.x(), geo.y(), geo.width(), geo.height()]
        self.settings.set("window_geometry", geometry)

        self.settings.set(
            "last_active_playlist_index",
            self.playlist_ui_manager.tab_widget.currentIndex(),
        )

        self.playlist_ui_manager.playlist_manager.save_playlists()
        self.playlist_ui_manager.tab_widget.update_tab_column_widths()

        self.save_column_managers()

        # current_volume = volume_slider.value()

        self.settings.save()

    def setup_icon_bar(self) -> None:
        for action in self.actions_:
            self.icon_bar.addAction(action)

        self.icon_bar.addSeparator()

        # Add volume slider
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.setValue(0)
        self.progress_slider.setToolTip("Playback Progress")
        # progress_slider.valueChanged.connect(self.on_progress_changed)
        self.icon_bar.addWidget(self.progress_slider)

        self.progress_slider.sliderMoved.connect(self.player_control_manager.on_seek)

        self.icon_bar.addSeparator()

        # Add progess slider
        volume_slider = QSlider(Qt.Orientation.Horizontal)
        volume_slider.setRange(0, 100)
        volume_slider.setValue(50)
        volume_slider.setToolTip("Volume")
        volume_slider.setMaximumWidth(100)

        volume_slider.sliderMoved.connect(self.player_control_manager.on_volume_changed)
        self.icon_bar.addWidget(volume_slider)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.save_settings()
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
