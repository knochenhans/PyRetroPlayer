import os
import time
import wave

from loguru import logger
from pydub import AudioSegment
from SettingsManager import SettingsManager

from PyRetroPlayer.player_backends.player_backend import PlayerBackend
from PyRetroPlayer.player_thread.base_player_thread import BasePlayerThread
from PyRetroPlayer.playing.player_events import PlayerEvents


class RecorderPlayerThread(BasePlayerThread):
    def __init__(
        self,
        player_backend: PlayerBackend,
        settings_manager: SettingsManager,
        events: PlayerEvents,
        filename: str,
        sample_rate: int = 44100,
        channels: int = 2,
    ) -> None:
        super().__init__(player_backend, settings_manager, events)

        self.filename = filename
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffersize = (
            1024 * self.channels * 2
        )  # 1024 samples per channel, 16-bit audio

    def run(self) -> None:
        self.player_backend.prepare_playing()
        module_length = self.player_backend.get_module_length()

        count: int = 0

        silence_length_ms: float = 0.0

        with wave.open(self.filename, "wb") as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit = 2 bytes
            wav_file.setframerate(self.sample_rate)

            while not self.stop_flag.is_set():
                if self.pause_flag.is_set():
                    time.sleep(0.1)
                    continue

                count, buffer = self.player_backend.read_chunk(
                    self.sample_rate, self.buffersize
                )
                if count == 0:
                    break

                # check if only contains silence
                if not any(buffer):
                    silence_length_ms += (
                        len(buffer) / (self.sample_rate * self.channels * 2) * 1000
                    )
                    if silence_length_ms > self.max_silence_length_ms:
                        count = 0
                        break
                else:
                    silence_length_ms = 0

                wav_file.writeframes(buffer)

                current_position = self.player_backend.get_position_milliseconds()
                if not self.stop_flag.is_set():
                    self.events.position_changed.emit(current_position, module_length)

        if count == 0:
            self.events.song_finished.emit()

        self.player_backend.free_module()

        logger.debug(f"Recording finished, saved to {self.filename}")

        # Convert finished file to configured format if needed
        format = self.settings_manager.get("default_record_format", "wav").lower()
        mp3_bitrate = self.settings_manager.get("mp3_bitrate", "320k")
        ogg_quality = self.settings_manager.get("ogg_quality", "5")

        if format != "wav":
            logger.debug(f"Converting recorded file to {format}")
            audio = AudioSegment.from_wav(self.filename)
            output_filename = self.filename.rsplit(".", 1)[0] + f".{format}"
            if format == "mp3":
                audio.export(
                    output_filename,
                    format=format,
                    codec="libmp3lame",
                    bitrate=mp3_bitrate,
                )
            elif format == "ogg":
                audio.export(
                    output_filename,
                    format=format,
                    codec="libvorbis",
                    parameters=["-aq", str(ogg_quality), "-ar", str(self.sample_rate)],
                )
            else:
                audio.export(output_filename, format=format)

            try:
                os.remove(self.filename)
            except Exception as e:
                logger.debug(f"Error removing original wav file: {e}")

            logger.debug(f"Conversion finished, saved to {output_filename}")
