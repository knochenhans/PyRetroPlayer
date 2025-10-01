import threading
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional

from loaders.abstract_loader import AbstractLoader  # type: ignore
from loguru import logger
from player_backends.player_backend import PlayerBackend  # type: ignore

from playlist.song import Song  # type: ignore


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
        self,
        song: Song,
        player_backends: Dict[str, Callable[[], PlayerBackend]],
        player_backends_priority: List[str],
        emitter: SongEmitter,
    ):
        self.song = song
        self.player_backends = player_backends
        self.player_backends_priority = player_backends_priority
        self.emitter = emitter

    def test_backends(self) -> None:
        # Sort backends by priority, fallback to others
        sorted_backend_names = [
            name
            for name in self.player_backends_priority
            if name in self.player_backends
        ]
        sorted_backend_names += [
            name for name in self.player_backends if name not in sorted_backend_names
        ]
        self.song.available_backends = []
        info_retrieved = False
        for backend_name in sorted_backend_names:
            backend_factory = self.player_backends[backend_name]
            logger.debug(f"Trying player backend: {backend_name}")

            player_backend = backend_factory()
            player_backend.song = self.song
            if player_backend.check_module():
                self.song.available_backends.append(backend_name)
                if not info_retrieved:
                    player_backend.retrieve_song_info()
                    self.song = player_backend.song
                    self.emitter.song_info_retrieved(self.song)
                    info_retrieved = True
                player_backend.cleanup()
        if not self.song.available_backends:
            self.song.available_backends = []
            logger.warning(
                f"No available backends found for song: {self.song.file_path}, song cannot be played."
            )
        self.emitter.song_checked(self.song)


class LocalFileLoaderWorker:
    def __init__(
        self,
        song: Song,
        player_backends: Dict[str, Callable[[], PlayerBackend]],
        player_backends_priority: List[str],
        loader: "LocalFileLoader",
    ) -> None:
        self.song: Song = song
        self.player_backends: Dict[str, Callable[[], PlayerBackend]] = player_backends
        self.player_backends_priority: List[str] = player_backends_priority
        self.loader = weakref.ref(loader)
        self.emitter = SongEmitter(
            self.song_checked_callback, self.song_info_retrieved_callback
        )

    def __call__(self) -> None:
        if self.song:
            tester = ModuleTester(
                self.song,
                self.player_backends,
                self.player_backends_priority,
                self.emitter,
            )
            tester.test_backends()
            loader = self.loader()
            if loader:
                loader.song_finished_loading()

    def song_checked_callback(self, song: Song) -> None:
        loader = self.loader()
        if loader and loader.song_loaded_callback:
            loader.song_loaded_callback(song)

    def song_info_retrieved_callback(self, song: Song) -> None:
        loader = self.loader()
        if loader and loader.song_info_retrieved_callback:
            loader.song_info_retrieved_callback(song)


class LocalFileLoader(AbstractLoader):
    def __init__(
        self,
        player_backends: Dict[str, Callable[[], PlayerBackend]],
        player_backends_priority: List[str],
    ) -> None:
        super().__init__(player_backends, player_backends_priority)

        max_workers = min(4, (threading.active_count() or 1) + 4)
        self.loading_thread: Optional[threading.Thread] = None
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.mutex = threading.Lock()

    def reset(self) -> None:
        self.loading_thread = None
        return super().reset()

    def start_loading(self) -> None:
        self.loading_thread = threading.Thread(target=self.load_songs)
        self.loading_thread.start()

    def load_songs(self) -> None:
        for file_name in self.file_list:
            song = self.load_song(file_name)
            if song:
                worker = LocalFileLoaderWorker(
                    song, self.player_backends, self.player_backends_priority, self
                )
                self.executor.submit(worker)

    def load_song(self, file_path: str) -> Optional[Song]:
        logger.debug(f"LocalFileLoader: Loading file: {file_path}")

        if file_path:
            song: Song = Song()
            song.file_path = file_path
            song.is_ready = True
            return song
        return None

    def update_song_info(self, song: Song) -> Optional[Song]:
        logger.debug(f"LocalFileLoader: Retrieving filename for song: {song.file_path}")
        song.title = song.file_path.split("/")[-1]  # Extract filename as the title
        return song

    def song_finished_loading(self) -> None:
        with self.mutex:
            self.songs_loaded += 1
            if self.songs_loaded == self.songs_to_load:
                if self.all_songs_loaded_callback:
                    self.all_songs_loaded_callback()
