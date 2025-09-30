import os
import sys
from typing import Any, Dict, List, Optional

from appdirs import user_config_dir, user_data_dir  # type: ignore
from audio_backends.pyaudio.audio_backend_pyuadio import (  # type: ignore
    AudioBackendPyAudio,
)
from player_backends.fake_player_backend import FakePlayerBackend  # type: ignore
from playlist.playlist import Playlist  # type: ignore
from playlist.song import Song  # type: ignore
from playlist.song_library import SongLibrary  # type: ignore
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent  # type: ignore
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSlider,
    QToolBar,
)
from settings.settings import Settings  # type: ignore


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

        self.configuration: Settings = Settings(
            "configuration",
            self.config_dir,
            self.application_name,
        )
        self.configuration.ensure_default_config()
        self.configuration.load()

        self.setWindowTitle(f"{self.application_name} v{self.application_version}")

        self.song_library = SongLibrary(os.path.join(self.data_dir, "song_library.db"))

        self.player_backends: Dict[str, Any] = {
            "FakeBackend": lambda: FakePlayerBackend()
        }

        self.audio_backends: Dict[str, Any] = {"PyAudio": lambda: AudioBackendPyAudio()}
        self.audio_backend = self.audio_backends["PyAudio"]()

        from player_control_manager import PlayerControlManager  # type: ignore

        self.player_control_manager = PlayerControlManager(self)

        from actions_manager import ActionsManager  # type: ignore

        self.actions_: List[QAction] = ActionsManager.get_actions_by_names(
            self.player_control_manager, ["play", "pause", "stop", "previous", "next"]
        )

        from file_manager import FileManager  # type: ignore
        from playlist_ui_manager import PlaylistUIManager  # type: ignore
        from ui_manager import UIManager  # type: ignore

        self.ui_manager = UIManager(self)
        self.file_manager = FileManager(self)
        self.playlist_ui_manager = PlaylistUIManager(self)

        self.ui_manager.create_menu_bar()

        self.icon_bar = QToolBar("Main Toolbar", self)
        self.addToolBar(self.icon_bar)

        self.setup_icon_bar()

        self.load_settings()

    def load_settings(self) -> None:
        geometry = self.configuration.get("window_geometry")
        if geometry:
            try:
                x, y, w, h = geometry
                self.setGeometry(x, y, w, h)
            except Exception:
                pass

        last_active_playlist_index = self.configuration.get(
            "last_active_playlist_index", 0
        )
        self.playlist_ui_manager.tab_widget.setCurrentIndex(last_active_playlist_index)

    def save_settings(self) -> None:
        geo = self.geometry()
        geometry = [geo.x(), geo.y(), geo.width(), geo.height()]
        self.configuration.set("window_geometry", geometry)

        current_tab_index = self.playlist_ui_manager.tab_widget.currentIndex()

        self.configuration.set("last_active_playlist_index", current_tab_index)

        self.playlist_ui_manager.playlist_manager.save_playlists()
        self.playlist_ui_manager.tab_widget.update_tab_column_widths()

        self.save_column_managers()

        # current_volume = volume_slider.value()

        self.configuration.save()

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
