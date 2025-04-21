from typing import Callable

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMenuBar, QVBoxLayout, QWidget


class UIManager:
    def __init__(self, main_window) -> None:
        self.main_window = main_window

    def setup_central_widget(self) -> QVBoxLayout:
        central_widget: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout(central_widget)
        self.main_window.setCentralWidget(central_widget)
        return layout

    def add_menu_action(
        self, menu: QMenu | QMenuBar, name: str, callback: Callable[[], None]
    ) -> None:
        action: QAction = QAction(name, self.main_window)
        action.triggered.connect(callback)
        menu.addAction(action)

    def create_menu_bar(self) -> QMenuBar:
        menu_bar: QMenuBar = self.main_window.menuBar()

        file_menu = menu_bar.addMenu("&File")

        self.add_menu_action(file_menu, "Add &Files...", self.main_window.add_files)
        self.add_menu_action(file_menu, "Add &Folder...", self.main_window.add_folder)

        file_menu.addSeparator()

        self.add_menu_action(
            file_menu, "&New Playlist", self.main_window.create_new_playlist
        )
        self.add_menu_action(
            file_menu, "&Import Playlist", self.main_window.import_playlist
        )
        self.add_menu_action(
            file_menu, "&Export Playlist", self.main_window.export_playlist
        )
        self.add_menu_action(
            file_menu, "&Delete Playlist", self.main_window.on_delete_playlist
        )

        file_menu.addSeparator()

        self.add_menu_action(file_menu, "E&xit", self.main_window.close)

        return menu_bar
