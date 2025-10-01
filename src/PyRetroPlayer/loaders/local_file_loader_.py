import weakref
import threading
from typing import Callable, List, Optional
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

from player_backends.player_backend import PlayerBackend
from playlist.song import Song


class SongEmitter:
    def __init__(
        self,
        song_checked: Callable[[Song], None],
        song_info_retrieved: Callable[[Song], None],
    ):
        self.song_checked = song_checked
        self.song_info_retrieved = song_info_retrieved


class ModuleTester:
    def __init__(
        self, song: Song, backends: dict[str, type[PlayerBackend]], emitter: SongEmitter
    ):
        self.song = song
        self.backends = backends
        self.emitter = emitter

    def test_backends(self) -> None:
        for backend_name, backend_class in self.backends.items():
            logger.debug(f"Trying player backend: {backend_name}")

            player_backend = backend_class(backend_name)
            player_backend.song = self.song
            if player_backend.check_module():
                logger.debug(f"Module loaded with player backend: {backend_name}")

                self.song.available_backends = backend_name
                player_backend.retrieve_song_info()
                self.song = player_backend.song
                self.emitter.song_info_retrieved(self.song)
                player_backend.cleanup()
                break
        self.emitter.song_checked(self.song)


class LocalFileLoaderWorker:
    def __init__(
        self,
        song: Song,
        backends: dict[str, type[PlayerBackend]],
        loader: "LocalFileLoader",
    ) -> None:
        self.song: Song = song
        self.player_backends: dict[str, type[PlayerBackend]] = backends
        self.loader = weakref.ref(loader)
        self.emitter = SongEmitter(
            self.song_checked_callback, self.song_info_retrieved_callback
        )

    def __call__(self) -> None:
        if self.song:
            tester = ModuleTester(self.song, self.player_backends, self.emitter)
            tester.test_backends()
            loader = self.loader()
            if loader:
                loader.song_finished_loading()

    def song_checked_callback(self, song: Song) -> None:
        loader = self.loader()
        if loader and loader.song_loaded:
            loader.song_loaded(song)

    def song_info_retrieved_callback(self, song: Song) -> None:
        loader = self.loader()
        if loader and loader.song_info_retrieved:
            loader.song_info_retrieved(song)


class LocalFileLoader:
    def __init__(
        self,
        file_list: List[str],
        player_backends: dict[str, type[PlayerBackend]],
        max_workers: int = 1,  # mimic QThreadPool(1)
    ) -> None:
        self.file_list = file_list
        self.player_backends = player_backends
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.songs_to_load = len(file_list)
        self.songs_loaded = 0
        self.mutex = threading.Lock()

        # Callbacks (replace Qt signals)
        self.song_loaded: Optional[Callable[[Song], None]] = None
        self.song_info_retrieved: Optional[Callable[[Song], None]] = None
        self.all_songs_loaded: Optional[Callable[[], None]] = None

    def load_module(self, filename: str) -> Optional[Song]:
        if filename:
            song: Song = Song()
            song.file_path = filename
            song.is_ready = True
            return song
        return None

    def load_songs(self) -> None:
        for file_name in self.file_list:
            song = self.load_module(file_name)
            if song:
                worker = LocalFileLoaderWorker(song, self.player_backends, self)
                self.executor.submit(worker)

    def song_finished_loading(self) -> None:
        with self.mutex:
            self.songs_loaded += 1
            if self.songs_loaded == self.songs_to_load:
                if self.all_songs_loaded:
                    self.all_songs_loaded()
