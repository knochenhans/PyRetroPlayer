from typing import List

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QMenu,
    QSystemTrayIcon,
)

from PyRetroPlayer.main_window import MainWindow


class TrayManager:
    def __init__(self, main_window: MainWindow) -> None:
        self.main_window = main_window

        self.tray_icon: QSystemTrayIcon
        self.tray_menu: QMenu

        self.setup_tray()

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

        from PyRetroPlayer.UI.actions_manager import ActionsManager

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

    def tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self.main_window.show()
