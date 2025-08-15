from typing import Callable

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMenuBar, QVBoxLayout, QWidget, QProgressBar


class UIManager:
    def __init__(self, main_window) -> None:
        self.main_window = main_window
        self.progress_bar: QProgressBar

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

    def create_library_menu(self, menu_bar: QMenuBar) -> None:
        library_menu = menu_bar.addMenu("&Library")

        self.add_menu_action(
            library_menu, "&Remove Missing Files", self.main_window.remove_missing_files
        )
