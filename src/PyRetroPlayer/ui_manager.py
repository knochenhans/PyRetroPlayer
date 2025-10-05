from typing import Callable, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QLabel,
    QMenu,
    QMenuBar,
    QProgressBar,
    QSystemTrayIcon,
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

    def setup_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self.main_window)
        self.tray_icon.setIcon(QIcon.fromTheme("media-playback-start"))

        # Create tray menu
        self.tray_menu = self.create_tray_menu()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # Minimize to tray
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.main_window.hide()

    def create_tray_menu(self) -> QMenu:
        tray_menu = QMenu(self.main_window)

        from PyRetroPlayer.actions_manager import ActionsManager

        actions: List[QAction] = ActionsManager.get_actions_by_names(
            self.main_window,
            [
                "play",
                "pause",
                "stop",
                "previous",
                "next",
            ],
        )

        # Reparent actions to tray_menu before adding
        for action in actions:
            action.setParent(tray_menu)
            tray_menu.addAction(action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self.main_window)
        quit_action.triggered.connect(self.main_window.close)
        tray_menu.addAction(quit_action)

        return tray_menu

    def show_tray_notification(self, title: str, message: str) -> None:
        self.tray_icon.showMessage(
            title,
            message,
            self.main_window.icon,
            10000,
        )
        self.tray_icon.setToolTip(message)

    def update_window_title(self, title: str) -> None:
        self.main_window.setWindowTitle(
            f"{self.main_window.application_name} - {title}"
        )

    def tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.main_window.show()
