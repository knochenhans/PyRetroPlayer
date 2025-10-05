import os
import sys
import threading
import webbrowser
from typing import Any, Dict, List, Optional

from appdirs import user_config_dir, user_data_dir
from mpris_server import Metadata
from mpris_server.adapters import MprisAdapter
from mpris_server.events import EventAdapter
from mpris_server.server import Server
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QIcon
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
from PyRetroPlayer.web_helper import WebHelper


class PlayerController:
    def __init__(self):
        self.state = "Stopped"  # or "Playing", "Paused"
        self.track_title = ""
        self.track_id = "track0"

    def play(self):
        print("Play called")
        self.state = "Playing"
        # your code to start / resume playing

    def pause(self):
        print("Pause called")
        self.state = "Paused"
        # code to pause

    def stop(self):
        print("Stop called")
        self.state = "Stopped"
        # code to stop

    def next(self):
        print("Next called")
        # code to skip

    def get_metadata(self) -> Dict[str, Any]:
        # Return metadata needed for MPRIS
        return {
            "mpris:trackid": f"/org/mpris/MediaPlayer2/Track/{self.track_id}",
            "xesam:title": self.track_title,
            "mpris:artUrl": "",
            "mpris:length": 0,  # length in microseconds
            "xesam:artist": ["Unknown"],
        }

    def get_playback_status(self):
        return (
            "Playing"
            if self.state == "Playing"
            else "Paused" if self.state == "Paused" else "Stopped"
        )


class MyAdapter(MprisAdapter):
    def __init__(self, controller: PlayerController):
        super().__init__()
        self.controller = controller

    # Capabilities: must be methods that return bool
    def can_go_next(self) -> bool:
        return True

    def can_play(self) -> bool:
        return True

    def can_pause(self) -> bool:
        return True

    def can_stop(self) -> bool:
        return True

    # Core metadata and state
    def metadata(self) -> Metadata:
        return Metadata(**self.controller.get_metadata())

    def playback_status(self) -> str:
        state = self.controller.get_playback_status()
        if state is None:
            return "Stopped"  # Default fallback
        if state.lower() in ("playing", "play"):
            return "Playing"
        elif state.lower() in ("paused", "pause"):
            return "Paused"
        else:
            return "Stopped"

    # Playback actions
    def play(self) -> None:
        self.controller.play()

    def pause(self) -> None:
        self.controller.pause()

    def stop(self) -> None:
        self.controller.stop()

    def next(self) -> None:
        self.controller.next()


def start_mpris(controller: PlayerController) -> tuple[Server, MprisAdapter]:
    adapter = MyAdapter(controller)
    mpris: Server = Server("PyRetroPlayer", adapter=adapter)

    # Run the D-Bus server in its own thread or in main loop
    thread = threading.Thread(target=mpris.loop, daemon=True)
    thread.start()

    return (mpris, adapter)


class MainWindow(QMainWindow):
    progress_bar_value_changed = Signal(int)

    def __init__(self) -> None:
        super().__init__()

        self.application_name: str = "PyRetroPlayer"
        self.application_version: str = "0.1.0"
        self.icon = QIcon.fromTheme("media-playback-start")
        self.setWindowIcon(self.icon)

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

        self.setWindowTitle(f"{self.application_name} v{self.application_version}")

        self.song_library = SongLibrary(os.path.join(self.data_dir, "song_library.db"))

        self.player_backends: Dict[str, Any] = {
            "LibUADE": lambda: PlayerBackendLibUADE(),
            "LibOpenMPT": lambda: PlayerBackendLibOpenMPT(),
            # "FakeBackend": lambda: FakePlayerBackend(),
        }
        self.player_backends_priorities: List[str] = [
            "LibUADE",
            "LibOpenMPT",
            # "FakeBackend",
        ]

        self.audio_backends: Dict[str, Any] = {"PyAudio": lambda: AudioBackendPyAudio()}
        self.audio_backend = self.audio_backends["PyAudio"]()

        from PyRetroPlayer.file_manager import FileManager
        from PyRetroPlayer.player_control_manager import PlayerControlManager
        from PyRetroPlayer.playlist_ui_manager import PlaylistUIManager
        from PyRetroPlayer.ui_manager import UIManager

        self.ui_manager = UIManager(self)
        self.playlist_ui_manager = PlaylistUIManager(self)
        self.player_control_manager = PlayerControlManager(
            self,
            self.settings,
            play_callback=self.playlist_ui_manager.on_playback_started,
            stop_callback=self.playlist_ui_manager.on_playback_stopped,
            pause_callback=self.playlist_ui_manager.on_playback_paused,
        )
        self.file_manager = FileManager(self)

        self.web_helper = WebHelper()

        from PyRetroPlayer.actions_manager import ActionsManager

        self.actions_: List[QAction] = ActionsManager.get_actions_by_names(
            self,
            [
                "play",
                "pause",
                "stop",
                "previous",
                "next",
                "song_info_dialog",
                "get_random_module",
                "lookup_modarchive",
                "lookup_msm",
            ],
        )

        self.playlist_ui_manager.setup_actions()

        self.ui_manager.create_menu_bar()

        self.icon_bar = QToolBar("Main Toolbar", self)
        self.addToolBar(self.icon_bar)

        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.ui_manager.setup_icon_bar()

        self.load_settings()
        self.ui_manager.setup_tray()

        controller = PlayerController()
        mpris, adapter = start_mpris(controller)

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

    def on_lookup_modarchive(self) -> None:
        current_tree_view = self.playlist_ui_manager.get_current_tree_view()
        if current_tree_view is None:
            return

        current_song = current_tree_view.get_current_song()

        if current_song is None:
            return

        url = self.web_helper.lookup_modarchive_mod_url(current_song)

        if url:
            webbrowser.open(url)

    def on_lookup_msm(self) -> None:
        current_tree_view = self.playlist_ui_manager.get_current_tree_view()
        if current_tree_view is None:
            return

        current_song = current_tree_view.get_current_song()

        if current_song is None:
            return

        url = self.web_helper.lookup_msm_mod_url(current_song)

        if url:
            webbrowser.open(url)


if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
