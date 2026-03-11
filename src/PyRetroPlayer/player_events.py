from PySide6.QtCore import QObject, Signal


class PlayerEvents(QObject):
    position_changed = Signal(int, int)
    song_finished = Signal()
