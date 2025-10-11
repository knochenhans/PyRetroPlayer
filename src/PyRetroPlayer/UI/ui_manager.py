from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QLabel,
    QMenu,
    QMenuBar,
    QProgressBar,
    QSlider,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from PyRetroPlayer.main_window import MainWindow
from PyRetroPlayer.UI.font_manager import FontManager


class UIManager:
    def __init__(self, main_window: MainWindow) -> None:
        self.main_window = main_window
        self.icon_bar: QToolBar
        self.loading_progress_bar: QProgressBar
        self.song_progress_slider: QSlider
        self.volume_slider: QSlider
        self.time_label: QLabel

        self.setup_central_widget()

        self.font_manager = FontManager()

    def setup_central_widget(self) -> None:
        central_widget: QWidget = QWidget()
        self.layout: QVBoxLayout = QVBoxLayout(central_widget)
        self.main_window.setCentralWidget(central_widget)

        self.content_layout: QVBoxLayout = QVBoxLayout()
        self.layout.addLayout(self.content_layout)

        self.song_progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)

        self.loading_progress_bar = QProgressBar()
        self.loading_progress_bar.setMinimum(0)
        self.loading_progress_bar.setMaximum(100)
        self.loading_progress_bar.setValue(0)
        self.loading_progress_bar.setVisible(False)

        self.layout.addWidget(self.loading_progress_bar)

    def add_widget(self, widget: QWidget) -> None:
        self.content_layout.addWidget(widget)

    def add_menu_action(
        self, menu: QMenu | QMenuBar, name: str, callback: Callable[[], None]
    ) -> None:
        action: QAction = QAction(name, self.main_window)
        action.triggered.connect(callback)
        menu.addAction(action)

    def create_menu_bar(self) -> QMenuBar:
        menu_bar: QMenuBar = self.main_window.menuBar()
        self.create_file_menu(menu_bar)
        self.create_library_menu(menu_bar)
        return menu_bar

    def create_file_menu(self, menu_bar: QMenuBar) -> None:
        file_menu = menu_bar.addMenu("&File")

        self.add_menu_action(
            file_menu, "Add &Files...", self.main_window.file_manager.add_files
        )
        self.add_menu_action(
            file_menu, "Add &Folder...", self.main_window.file_manager.add_folder
        )

        file_menu.addSeparator()

        self.add_menu_action(
            file_menu,
            "&New Playlist",
            self.main_window.playlist_ui_manager.create_new_playlist,
        )
        self.add_menu_action(
            file_menu,
            "&Import Playlist",
            self.main_window.playlist_ui_manager.import_playlist,
        )
        self.add_menu_action(
            file_menu,
            "&Export Playlist",
            self.main_window.playlist_ui_manager.export_playlist,
        )
        self.add_menu_action(
            file_menu,
            "&Delete Playlist",
            self.main_window.playlist_ui_manager.on_delete_playlist,
        )

        file_menu.addSeparator()

        self.add_menu_action(file_menu, "E&xit", self.main_window.close)  # type: ignore

    def create_library_menu(self, menu_bar: QMenuBar) -> None:
        library_menu = menu_bar.addMenu("&Library")

        self.add_menu_action(
            library_menu,
            "&Load All Songs",
            self.main_window.load_all_songs_from_library,
        )

        self.add_menu_action(
            library_menu, "&Remove Missing Files", self.main_window.remove_missing_files
        )

        self.add_menu_action(
            library_menu, "&Clear Song Library", self.main_window.clear_song_library
        )

    def update_song_progress_bar(self, current_position: int, song_length: int) -> None:
        if song_length > 0:
            self.song_progress_slider.setMaximum(song_length)
            self.song_progress_slider.setValue(current_position)

            self.update_time_label(current_position, song_length)

    def update_loading_progress_bar(self, current_value: int, total_value: int) -> None:
        if not self.loading_progress_bar.isVisible():
            self.loading_progress_bar.setVisible(True)

        self.loading_progress_bar.setValue(current_value)
        self.loading_progress_bar.setMaximum(total_value)
        
        if current_value >= total_value:
            self.loading_progress_bar.setVisible(False)

    def setup_icon_bar(self) -> None:
        self.icon_bar = QToolBar("Main Toolbar", self.main_window)
        self.main_window.addToolBar(self.icon_bar)

        for action in self.main_window.actions_:
            self.icon_bar.addAction(action)

        self.icon_bar.addSeparator()

        self.song_progress_slider.setRange(0, 100)
        self.song_progress_slider.setValue(0)
        self.song_progress_slider.setToolTip("Playback Progress")
        self.icon_bar.addWidget(self.song_progress_slider)

        # Add time label for 00:00/00:00 display
        self.time_label = QLabel("00:00/00:00")
        self.time_label.setMinimumWidth(80)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_bar.addWidget(self.time_label)

        self.song_progress_slider.sliderMoved.connect(
            self.main_window.player_control_manager.on_seek
        )

        self.icon_bar.addSeparator()

        # Add volume slider
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setToolTip("Volume")
        self.volume_slider.setMaximumWidth(100)

        self.volume_slider.sliderMoved.connect(
            self.main_window.player_control_manager.on_volume_changed
        )
        self.icon_bar.addWidget(self.volume_slider)

    def update_time_label(self, current_ms: int, total_ms: int) -> None:
        def format_time(ms: int) -> str:
            secs = ms // 1000
            mins = secs // 60
            secs = secs % 60
            return f"{mins:02}:{secs:02}"

        self.time_label.setText(f"{format_time(current_ms)}/{format_time(total_ms)}")

    def update_window_title(self, title: str) -> None:
        self.main_window.setWindowTitle(
            f"{self.main_window.application_name} - {title}"
        )
