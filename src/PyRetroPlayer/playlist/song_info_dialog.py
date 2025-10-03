from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QDialog, QTreeView, QVBoxLayout, QWidget

from PyRetroPlayer.playlist.song import Song


class SongInfoDialog(QDialog):
    def __init__(self, song: Song, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.song = song
        self.setWindowTitle("Song Information")
        self.setMinimumSize(400, 300)

        # Add ListView to display song information
        self.list_view = QTreeView(self)
        self.list_view.setRootIsDecorated(False)
        self.list_view.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.list_view.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.list_view.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.model = QStandardItemModel(0, 2, self)
        self.model.setHeaderData(0, Qt.Orientation.Horizontal, "Field")
        self.model.setHeaderData(1, Qt.Orientation.Horizontal, "Value")
        self.list_view.setModel(self.model)
        self.populate_model()
        self.list_view.resizeColumnToContents(0)

        # Use layout to make list view scale with dialog
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_view)
        self.setLayout(layout)

    def populate_model(self):
        fields = {
            "Title": self.song.title,
            "Artist": self.song.artist,
            "File Path": self.song.file_path,
            "Duration": (
                f"{self.song.duration // 1000} seconds"
                if self.song.duration
                else "Unknown"
            ),
            "Available Backends": (
                ", ".join(self.song.available_backends)
                if self.song.available_backends
                else "None"
            ),
            "MD5": self.song.md5 or "N/A",
            "SHA1": self.song.sha1 or "N/A",
        }
        for field, value in fields.items():
            field_item = QStandardItem(field)
            value_item = QStandardItem(value)
            self.model.appendRow([field_item, value_item])

        # Add custom metadata as individual rows
        def add_metadata_rows(
            key: str, value: str | List[str] | Dict[str, str], prefix: str = ""
        ):
            display_key = f"{prefix}{key.capitalize()}" if prefix else key.capitalize()
            if isinstance(value, dict):
                for subkey, subval in value.items():
                    add_metadata_rows(subkey, subval, prefix=f"{display_key}: ")
            elif isinstance(value, list):
                field_item = QStandardItem(display_key)
                value_item = QStandardItem(", ".join(map(str, value)))
                self.model.appendRow([field_item, value_item])
            else:
                field_item = QStandardItem(display_key)
                value_item = QStandardItem(str(value))
                self.model.appendRow([field_item, value_item])

        if self.song.custom_metadata:
            for key, value in self.song.custom_metadata.items():
                add_metadata_rows(key, value)
