import os
import sys
import webbrowser
from typing import Any, Dict, List, Optional

import dbus  # type: ignore
import dbus.mainloop.glib  # type: ignore
from appdirs import user_data_dir
from gi.repository import GLib  # type: ignore
from PySide6.QtCore import QThread, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
)
from SettingsManager import SettingsManager

from PyRetroPlayer.audio_backends.audio_backend_wav import AudioBackendWav
from PyRetroPlayer.audio_backends.pyaudio.audio_backend_pyuadio import (
    AudioBackendPyAudio,
)
from PyRetroPlayer.player_backends.libopenmpt.player_backend_libopenmpt import (
    PlayerBackendLibOpenMPT,
)
from PyRetroPlayer.player_backends.libuade.player_backend_libuade import (
    PlayerBackendLibUADE,
)
from PyRetroPlayer.player_thread.recorder_player_thread_manager import (
    RecorderPlayerThreadManager,
)
from PyRetroPlayer.playlist.playlist import Playlist
from PyRetroPlayer.playlist.playlist_entry import PlaylistEntry
from PyRetroPlayer.playlist.song import Song
from PyRetroPlayer.playlist.song_info_dialog import SongInfoDialog
from PyRetroPlayer.playlist.song_library import SongLibrary
from PyRetroPlayer.scraping.modarchive_scraper import ModArchiveScraper
from PyRetroPlayer.scraping.msm_scraper import MSMScraper
from PyRetroPlayer.web_helper import WebHelper


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.application_name: str = "PyRetroPlayer"
        self.application_version: str = "0.1.0"
        self.icon = QIcon.fromTheme("media-playback-start")
        self.setWindowIcon(self.icon)

        self.data_dir = os.path.join(user_data_dir(), self.application_name)
        os.makedirs(self.data_dir, exist_ok=True)

        SettingsManager.set_app_name(self.application_name)

        self.settings_manager: SettingsManager = SettingsManager(
            "configuration",
        )
        self.settings_manager.load()

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

        self.audio_backends: Dict[str, Any] = {
            "PyAudio": lambda: AudioBackendPyAudio(),
            "WAV": lambda: AudioBackendWav(),
        }
        self.audio_backend = self.audio_backends["PyAudio"]()

        from PyRetroPlayer.file_manager import FileManager
        from PyRetroPlayer.player_control_manager import PlayerControlManager
        from PyRetroPlayer.UI.playlist_ui_manager import PlaylistUIManager
        from PyRetroPlayer.UI.ui_manager import UIManager

        self.ui_manager = UIManager(self)
        self.playlist_ui_manager = PlaylistUIManager(self)
        self.player_control_manager = PlayerControlManager(
            self,
            self.settings_manager,
            play_callback=self.playlist_ui_manager.on_playback_started,
            stop_callback=self.playlist_ui_manager.on_playback_stopped,
            pause_callback=self.playlist_ui_manager.on_playback_paused,
        )
        self.file_manager = FileManager(self)

        self.web_helper = WebHelper()

        from PyRetroPlayer.UI.actions_manager import ActionsManager

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
                "download_favorites",
                "rescan_songs",
            ],
        )

        self.playlist_ui_manager.setup_actions()

        self.ui_manager.create_menu_bar()
        self.ui_manager.setup_icon_bar()

        self.load_settings()

        from PyRetroPlayer.UI.tray_manager import TrayManager

        self.tray_manager = TrayManager(self)

        self.modarchive_scraper = ModArchiveScraper()
        self.msm_scraper = MSMScraper()

    def load_settings(self) -> None:
        geometry = self.settings_manager.get("window_geometry")
        if geometry:
            try:
                x, y, w, h = geometry
                self.setGeometry(x, y, w, h)
            except Exception:
                pass

        self.playlist_ui_manager.tab_widget.setCurrentIndex(
            self.settings_manager.get("last_active_playlist_index", 0)
        )

    def save_settings(self) -> None:
        geo = self.geometry()
        geometry = [geo.x(), geo.y(), geo.width(), geo.height()]
        self.settings_manager.set("window_geometry", geometry)

        self.settings_manager.set(
            "last_active_playlist_index",
            self.playlist_ui_manager.tab_widget.currentIndex(),
        )

        self.playlist_ui_manager.playlist_manager.save_playlists()
        self.playlist_ui_manager.tab_widget.update_tab_column_widths()

        self.save_column_managers()

        self.settings_manager.save()

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

    def get_current_song(self) -> Optional[Song]:
        current_tree_view = self.playlist_ui_manager.get_current_tree_view()
        if current_tree_view is None:
            return None

        return current_tree_view.get_current_song()

    def on_lookup_modarchive(self) -> None:
        current_song = self.get_current_song()

        if current_song is None:
            return

        url = self.modarchive_scraper.get_url(current_song)

        if url:
            webbrowser.open(url)

    def on_lookup_msm(self) -> None:
        current_song = self.get_current_song()
        if current_song is None:
            return

        url = self.msm_scraper.get_url(current_song)

        if url:
            webbrowser.open(url)

    def download_favorite_modules(self) -> None:
        member_id = self.settings_manager.get("modarchive_member_id", 0)
        if member_id == 0:
            return

        favorites_dir = os.path.join(self.data_dir, "favorites")
        os.makedirs(favorites_dir, exist_ok=True)

        downloaded_files = self.web_helper.download_favorite_modules(
            member_id, favorites_dir
        )

        if downloaded_files:
            current_tree_view = self.playlist_ui_manager.get_current_tree_view()
            if current_tree_view is None:
                return

            current_index = self.playlist_ui_manager.tab_widget.currentIndex()
            if current_index == -1:
                return

            playlist = self.playlist_ui_manager.playlist_manager.playlists[
                current_index
            ]
            self.load_files(downloaded_files, playlist)

    def on_song_info_dialog(self) -> None:
        current_song = self.get_current_song()
        if current_song:
            dialog = SongInfoDialog(current_song, self.ui_manager.font_manager, self)
            dialog.exec()

    def get_selected_entries(self) -> List[PlaylistEntry]:
        current_tree_view = self.playlist_ui_manager.get_current_tree_view()
        if current_tree_view is None:
            return []

        return current_tree_view.get_selected_entries()

    def scan_selected_entries(self) -> None:
        self.scan_entries(self.get_selected_entries())

    def scan_entries(self, entries: List[PlaylistEntry]) -> None:
        from PyRetroPlayer.scan_entries_worker import ScanEntriesWorker

        self.scan_thread = QThread(self)
        self.scan_worker = ScanEntriesWorker(
            entries,
            self.song_library,
            self.file_manager,
            self.modarchive_scraper,
        )
        self.scan_worker.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.finished.connect(self.scan_thread.quit)
        self.scan_worker.finished.connect(self.scan_worker.deleteLater)
        self.scan_thread.finished.connect(self.scan_thread.deleteLater)
        self.scan_worker.entry_updated.connect(self.update_playlist_entry)
        self.scan_thread.start()

    def update_playlist_entry(
        self, entry: PlaylistEntry, current: int, total: int
    ) -> None:
        current_tree_view = self.playlist_ui_manager.get_current_tree_view()
        if current_tree_view is None:
            return

        current_tree_view.update_entry(entry)
        self.ui_manager.update_loading_progress_bar(current, total)

    def save_selected_entries_as_audio(self) -> None:
        selected_entries = self.get_selected_entries()
        song_ids = [entry.song_id for entry in selected_entries if entry.song_id != ""]

        for song_id in song_ids:
            song = self.song_library.get_song_by_id(song_id)
            if song:
                self.save_song_as_audio(song)

    def save_current_song_as_audio(self) -> None:
        current_song = self.get_current_song()
        if current_song:
            self.save_song_as_audio(current_song)

    def save_song_as_audio(self, song: Song) -> None:
        output_dir = self.settings_manager.get("default_record_path", self.data_dir)
        os.makedirs(output_dir, exist_ok=True)
        self.recorder_player_thread_manager = RecorderPlayerThreadManager(
            settings_manager=self.settings_manager,
            filename=os.path.join(output_dir, song.get_safe_filename() + ".wav"),
        )

        backend_name = song.available_backends[0]
        backend_factory = self.player_backends.get(backend_name)

        current_backend = None

        if backend_factory:
            current_backend = backend_factory()

        if current_backend:
            current_backend.load_song(song)

        if current_backend:
            self.recorder_player_thread_manager.start(current_backend)


def integrate_glib_loop() -> QTimer:
    context: GLib.MainContext = GLib.MainContext.default()  # type: ignore

    def iterate() -> None:  # type: ignore
        while context.pending():  # type: ignore
            context.iteration(False)  # type: ignore

    timer: QTimer = QTimer()
    timer.timeout.connect(iterate)
    timer.start(50)

    return timer


if __name__ == "__main__":
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)  # type: ignore

    app: QApplication = QApplication(sys.argv)

    glib_timer = integrate_glib_loop()

    window: MainWindow = MainWindow()
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())
