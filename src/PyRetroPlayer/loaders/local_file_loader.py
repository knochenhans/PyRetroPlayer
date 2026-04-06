import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Dict, List, Optional

from loguru import logger

from PyRetroPlayer.loaders.abstract_loader import AbstractLoader
from PyRetroPlayer.player_backends.player_backend import PlayerBackend
from PyRetroPlayer.playlist.loader_events import LoaderEvents
from PyRetroPlayer.playlist.song import Song


class LocalFileLoader(AbstractLoader):
    def __init__(
        self,
        player_backends: Dict[str, Callable[[], PlayerBackend]],
        player_backends_priority: List[str],
        max_workers: int = 1,
        events: Optional[LoaderEvents] = None,
    ) -> None:
        super().__init__(player_backends, player_backends_priority)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.mutex = threading.Lock()
        self._futures: List[Future[None]] = []
        self.semaphore = threading.Semaphore(max_workers)
        self.loader_events: LoaderEvents = events or LoaderEvents()

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
            self.semaphore.acquire()

            from PyRetroPlayer.loaders.local_file_loader_worker import (
                LocalFileLoaderWorker,
            )

            song = self.load_song_from_path(file_name)
            if song:
                worker = LocalFileLoaderWorker(
                    song,
                    self.player_backends,
                    self.player_backends_priority,
                    self,
                    self.loader_events,
                )
                future = self.executor.submit(worker)
                future.add_done_callback(self._release_semaphore)
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

    def _release_semaphore(self, fut: Future[None]) -> None:
        try:
            exc = fut.exception(timeout=0)
            if exc:
                logger.exception("Worker future raised: %s", exc)
        except Exception:
            pass
        finally:
            self.semaphore.release()

    def load_song_from_path(self, file_path: str) -> Optional[Song]:
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
