from typing import List

from PySide6.QtCore import QObject, Signal

from PyRetroPlayer.file_manager import FileManager
from PyRetroPlayer.playlist.playlist_entry import PlaylistEntry
from PyRetroPlayer.playlist.song_library import SongLibrary
from PyRetroPlayer.scraping.scraper import Scraper


class ScanEntriesWorker(QObject):
    finished = Signal()
    entry_updated = Signal(PlaylistEntry, int, int)

    def __init__(
        self,
        entries: List[PlaylistEntry],
        song_library: SongLibrary,
        file_manager: FileManager,
        modarchive_scraper: Scraper,
    ) -> None:
        super().__init__()
        self.entries = entries
        self.song_library = song_library
        self.file_manager = file_manager
        self.scraper = modarchive_scraper

    def run(self):
        total = len(self.entries)
        for i, entry in enumerate(self.entries):
            song = self.song_library.get_song(entry.song_id)
            if song is None:
                self.entry_updated.emit(entry, i + 1, total)
                continue
            self.file_manager.scan_song(song)
            self.scraper.scrape(song)
            self.scraper.apply_scraped_data_to_song(song)
            self.scraper.reset()
            self.song_library.update_song(song)
            self.entry_updated.emit(entry, i + 1, total)
        self.finished.emit()
