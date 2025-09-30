from loguru import logger
from player_backends.player_backend import PlayerBackend  # type: ignore


class FakePlayerBackend(PlayerBackend):
    def __init__(self, name: str = "FakePlayerBackend") -> None:
        super().__init__(name)
        self.current_position = 0
        self._sim_buffer = b"\x00" * (
            10 * 44100 * 2
        )  # 10 seconds at 44.1kHz, 16-bit mono
        self._sim_buffer_pos = 0

    def check_module(self) -> bool:
        """Simulate checking if the module can be loaded."""
        logger.debug(
            f"{self.name}: Checking module for song: {self.song.file_path if self.song else 'None'}"
        )

        is_playable = self.song is not None

        # check if file path exists and is a file
        if self.song and self.song.file_path:
            try:
                with open(self.song.file_path, "rb"):
                    pass
            except FileNotFoundError:
                is_playable = False
                logger.warning(f"{self.name}: File not found: {self.song.file_path}")

        return is_playable

    def prepare_playing(self, subsong_nr: int = -1) -> None:
        """Simulate preparing the module for playback."""

        if not self.song:
            logger.warning(f"{self.name}: No song loaded to prepare for playback.")
            return

        self.song.is_ready = self.check_module()

        if not self.song.is_ready:
            logger.warning(f"{self.name}: Module is not loaded.")
            return
        self.current_subsong = subsong_nr if subsong_nr >= 0 else 0
        logger.debug(
            f"{self.name}: Preparing playback for subsong {self.current_subsong}."
        )
        self._sim_buffer_pos = 0

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
        self.song.duration = (
            self.song.duration or 10000
        )  # Fake duration of 10 seconds as milliseconds

    def get_module_length(self) -> int:
        """Return the simulated module length."""
        if not self.song:
            logger.warning(f"{self.name}: No song loaded to get module length.")
            return 0
        return self.song.duration or 0

    def read_chunk(self, samplerate: int, buffersize: int) -> tuple[int, bytes]:
        if not self.song:
            logger.warning(f"{self.name}: No song loaded to read audio data.")
            return 0, b""

        if not self.song.is_ready:
            logger.warning(f"{self.name}: No module loaded to read audio data.")
            return 0, b""

        # Simulate reading from the 10-second buffer
        remaining = len(self._sim_buffer) - self._sim_buffer_pos
        to_read = min(buffersize, remaining)
        chunk = self._sim_buffer[self._sim_buffer_pos : self._sim_buffer_pos + to_read]
        self._sim_buffer_pos += to_read
        logger.debug(
            f"{self.name}: Reading {to_read} bytes of audio data at {samplerate} Hz."
        )
        self.current_position = int(
            (self._sim_buffer_pos / (44100 * 2)) * 1000
        )  # in milliseconds
        return to_read, chunk

    def get_position_milliseconds(self) -> int:
        """Return the current playback position."""
        return self.current_position

    def seek(self, position: int) -> None:
        """Simulate seeking to a specific position."""
        if position < 0 or position > self.get_module_length():
            logger.warning(f"{self.name}: Seek position {position} is out of bounds.")
            return
        self.current_position = position
        # Seek in simulated buffer
        byte_pos = int(position * 44100 * 2)  # position in milliseconds
        if byte_pos < 0 or byte_pos > len(self._sim_buffer):
            logger.warning(f"{self.name}: Seek position {position} is out of bounds.")
            return
        self._sim_buffer_pos = byte_pos
        logger.debug(
            f"{self.name}: Seeking to position {self.current_position} milliseconds."
        )

    def free_module(self) -> None:
        """Simulate freeing the loaded module."""
        logger.debug(f"{self.name}: Module freed.")
        self._sim_buffer_pos = 0

    def cleanup(self) -> None:
        """Simulate cleaning up resources."""
        self.current_position = 0
        self._sim_buffer_pos = 0
        logger.debug(f"{self.name}: Cleanup completed.")
