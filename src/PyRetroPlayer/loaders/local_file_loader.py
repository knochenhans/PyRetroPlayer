import threading
import traceback
import weakref
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Dict, List, Optional

from loguru import logger

from PyRetroPlayer.loaders.abstract_loader import AbstractLoader
from PyRetroPlayer.player_backends.player_backend import PlayerBackend
from PyRetroPlayer.playlist.song import Song


class SongEmitter:
    def __init__(
        self,
        song_checked: Callable[[Optional[Song]], None],
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
                try:
                    player_backend.cleanup()
                except Exception:
                    logger.exception("Error during backend.cleanup()")
        if not self.song.available_backends:
            self.song.available_backends = []
            logger.warning(
                f"No available backends found for song: {self.song.file_path}, song cannot be played."
            )
            self.emitter.song_checked(None)
            return
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
        # keep weakref to avoid reference cycles / lifetime issues
        self.loader = weakref.ref(loader)
        self.emitter = SongEmitter(
            self.song_checked_callback, self.song_info_retrieved_callback
        )

    def __call__(self) -> None:
        try:
            if self.song:
                tester = ModuleTester(
                    self.song,
                    self.player_backends,
                    self.player_backends_priority,
                    self.emitter,
                )
                tester.test_backends()
        except Exception:
            logger.exception(
                "Exception in LocalFileLoaderWorker for %s",
                getattr(self.song, "file_path", "<unknown>"),
            )
        finally:
            # Always notify loader that this song finished (success or failure)
            loader = self.loader()
            if loader:
                try:
                    loader.song_finished_loading()
                except Exception:
                    logger.exception("Exception in loader.song_finished_loading()")

    def song_checked_callback(self, song: Optional[Song]) -> None:
        loader = self.loader()
        if loader and loader.song_loaded_callback:
            try:
                loader.song_loaded_callback(song)
            except Exception:
                logger.exception("Exception in song_loaded_callback")

    def song_info_retrieved_callback(self, song: Song) -> None:
        loader = self.loader()
        if loader and loader.song_info_retrieved_callback:
            try:
                loader.song_info_retrieved_callback(song)
            except Exception:
                logger.exception("Exception in song_info_retrieved_callback")


class LocalFileLoader(AbstractLoader):
    def __init__(
        self,
        player_backends: Dict[str, Callable[[], PlayerBackend]],
        player_backends_priority: List[str],
        max_workers: int = 1,
    ) -> None:
        super().__init__(player_backends, player_backends_priority)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.mutex = threading.Lock()
        self._futures: List[Future[None]] = (
            []
        )  # keep futures so we can inspect/exceptions/shutdown

    def cleanup(self) -> None:
        # Shut down executor cleanly
        try:
            pass
            # optionally wait for tasks to finish; if you want to cancel, iterate and cancel futures
            self.executor.shutdown(wait=True)
        except Exception:
            logger.exception("Error shutting down ThreadPoolExecutor")
        finally:
            # create a new executor so loader remains usable after cleanup
            self.executor = ThreadPoolExecutor(max_workers=1)
            self._futures.clear()

    def start_loading(self) -> None:
        self.loading_thread = threading.Thread(target=self.load_songs, daemon=True)
        self.loading_thread.start()

    def load_songs(self) -> None:
        for file_name in self.file_list:
            song = self.load_song(file_name)
            if song:
                worker = LocalFileLoaderWorker(
                    song, self.player_backends, self.player_backends_priority, self
                )
                future = self.executor.submit(worker)
                # add done callback to log exceptions (optional)
                future.add_done_callback(self._future_done)
                self._futures.append(future)

    def _future_done(self, fut: Future[None]) -> None:
        # Force logging of exceptions from futures
        try:
            exc = fut.exception(timeout=0)
            if exc:
                logger.exception("Worker future raised an exception: %s", exc)
        except Exception:
            # fut.exception(timeout=0) raises if result not ready; ignore
            pass

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
        song.title = song.file_path.split("/")[-1]
        return song

    def song_finished_loading(self) -> None:
        with self.mutex:
            self.songs_loaded += 1
            if self.songs_loaded == self.songs_to_load:
                threading.Thread(target=self.all_songs_loaded_callback).start()
