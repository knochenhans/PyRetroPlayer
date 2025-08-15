from loguru import logger

from player_backends.player_backend import PlayerBackend


class FakePlayerBackend(PlayerBackend):
    def __init__(self, name: str = "FakePlayerBackend") -> None:
        super().__init__(name)
        self.is_module_loaded = False
        self.module_length = 180  # Simulate a 3-minute song
        self.current_position = 0.0

    def check_module(self) -> bool:
        """Simulate checking if the module can be loaded."""
        logger.debug(
            f"{self.name}: Checking module for song: {self.song.file_path if self.song else 'None'}"
        )
        self.is_module_loaded = True  # Simulate that the module can always be loaded
        return self.is_module_loaded

    def prepare_playing(self, subsong_nr: int = -1) -> None:
        """Simulate preparing the module for playback."""
        if not self.is_module_loaded:
            logger.warning(f"{self.name}: No module loaded to prepare for playback.")
            return
        self.current_subsong = subsong_nr if subsong_nr >= 0 else 0
        logger.debug(
            f"{self.name}: Preparing playback for subsong {self.current_subsong}."
        )

    def retrieve_song_info(self) -> None:
        """Simulate retrieving song metadata."""
        if not self.song:
            logger.warning(f"{self.name}: No song loaded to retrieve metadata.")
            return
        logger.debug(
            f"{self.name}: Retrieving metadata for song: {self.song.file_path}"
        )
        self.song.title = self.song.title or "Fake Song Title"
        self.song.artist = self.song.artist or "Fake Artist"
        self.song.duration = self.module_length

    def get_module_length(self) -> float:
        """Return the simulated module length."""
        return self.module_length

    def read_chunk(self, samplerate: int, buffersize: int) -> tuple[int, bytes]:
        """Simulate reading a chunk of audio data."""
        if not self.is_module_loaded:
            logger.warning(f"{self.name}: No module loaded to read audio data.")
            return 0, b""
        logger.debug(
            f"{self.name}: Reading {buffersize} bytes of audio data at {samplerate} Hz."
        )
        return buffersize, b"\x00" * buffersize  # Simulate a chunk of silence

    def get_position_seconds(self) -> float:
        """Return the current playback position."""
        return self.current_position

    def seek(self, position: int) -> None:
        """Simulate seeking to a specific position."""
        if position < 0 or position > self.module_length:
            logger.warning(f"{self.name}: Seek position {position} is out of bounds.")
            return
        self.current_position = position
        logger.debug(
            f"{self.name}: Seeking to position {self.current_position} seconds."
        )

    def free_module(self) -> None:
        """Simulate freeing the loaded module."""
        self.is_module_loaded = False
        logger.debug(f"{self.name}: Module freed.")

    def cleanup(self) -> None:
        """Simulate cleaning up resources."""
        self.is_module_loaded = False
        self.current_position = 0.0
        logger.debug(f"{self.name}: Cleanup completed.")
