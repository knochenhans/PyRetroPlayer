from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QLabel,
    QMenu,
    QMenuBar,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from PyRetroPlayer.main_window import MainWindow


class UIManager:
    def __init__(self, main_window: MainWindow) -> None:
        self.main_window = main_window
        self.progress_bar: QProgressBar
        self.time_label: QLabel  # Add time label attribute

        self.setup_central_widget()

    def setup_central_widget(self) -> None:
        central_widget: QWidget = QWidget()
        self.layout: QVBoxLayout = QVBoxLayout(central_widget)
        self.main_window.setCentralWidget(central_widget)

        self.content_layout: QVBoxLayout = QVBoxLayout()
        self.layout.addLayout(self.content_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)
        self.progress_bar.setVisible(False)

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

    def update_progress_bar(self, current_position: int, module_length: int) -> None:
        if module_length > 0:
            self.main_window.progress_slider.setMaximum(module_length)
            self.main_window.progress_slider.setValue(current_position)
            # self.progress_bar.update()

            self.update_time_label(current_position, module_length)

    def setup_icon_bar(self) -> None:
        for action in self.main_window.actions_:
            self.main_window.icon_bar.addAction(action)

        self.main_window.icon_bar.addSeparator()

        # Add progress slider
        # self.main_window.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.main_window.progress_slider.setRange(0, 100)
        self.main_window.progress_slider.setValue(0)
        self.main_window.progress_slider.setToolTip("Playback Progress")
        # progress_slider.valueChanged.connect(self.on_progress_changed)
        self.main_window.icon_bar.addWidget(self.main_window.progress_slider)

        # Add time label for 00:00/00:00 display
        self.time_label = QLabel("00:00/00:00")
        self.time_label.setMinimumWidth(80)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_window.icon_bar.addWidget(self.time_label)

        self.main_window.progress_slider.sliderMoved.connect(
            self.main_window.player_control_manager.on_seek
        )

        self.main_window.icon_bar.addSeparator()

        # Add volume slider
        # self.main_window.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.main_window.volume_slider.setRange(0, 100)
        self.main_window.volume_slider.setValue(50)
        self.main_window.volume_slider.setToolTip("Volume")
        self.main_window.volume_slider.setMaximumWidth(100)

        self.main_window.volume_slider.sliderMoved.connect(
            self.main_window.player_control_manager.on_volume_changed
        )
        self.main_window.icon_bar.addWidget(self.main_window.volume_slider)

    def update_time_label(self, current_ms: int, total_ms: int) -> None:
        def format_time(ms: int) -> str:
            secs = ms // 1000
            mins = secs // 60
            secs = secs % 60
            return f"{mins:02}:{secs:02}"

        self.time_label.setText(f"{format_time(current_ms)}/{format_time(total_ms)}")
