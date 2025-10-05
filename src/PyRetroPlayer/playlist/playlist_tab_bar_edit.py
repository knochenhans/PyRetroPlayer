from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QFocusEvent, QKeyEvent
from PySide6.QtWidgets import QLineEdit

from PyRetroPlayer.playlist.playlist_tab_widget import PlaylistTabWidget


class PlaylistTabBarEdit(QLineEdit):
    def __init__(self, parent: PlaylistTabWidget, rect: QRect) -> None:
        super().__init__(parent)

        tabBar = parent.tabBar()

        from PyRetroPlayer.playlist.playlist_tab_bar import PlaylistTabBar

        if not isinstance(tabBar, PlaylistTabBar):
            return

        self.setGeometry(rect)
        self.textChanged.connect(tabBar.rename)
        self.editingFinished.connect(tabBar.editing_finished)
        self.returnPressed.connect(self.close)

    def focusOutEvent(self, arg__1: QFocusEvent) -> None:
        parent = self.parent()

        from PyRetroPlayer.playlist.playlist_tab_widget import PlaylistTabWidget

        if isinstance(parent, PlaylistTabWidget):
            tab_bar = parent.tabBar()

            from PyRetroPlayer.playlist.playlist_tab_bar import PlaylistTabBar

            if isinstance(tab_bar, PlaylistTabBar):
                tab_bar.editing_finished()
                self.close()

    def keyPressEvent(self, arg__1: QKeyEvent) -> None:
        if arg__1.key() == Qt.Key.Key_Escape:
            self.close()

        super().keyPressEvent(arg__1)
