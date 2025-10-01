import ctypes
import sys
import warnings
from typing import List, Optional, Tuple

from loguru import logger

sys.path.append("../libopenmpt_py")

from libopenmpt_py import libopenmpt  # type: ignore
from player_backends.player_backend import PlayerBackend  # type: ignore


def log_callback(user_data: Optional[ctypes.c_void_p], level: int, message: str):
    print(f"Log: {message}")


def error_callback(user_data: Optional[ctypes.c_void_p], message: str):
    print(f"Error: {message}")


def print_error(
    func_name: Optional[str],
    mod_err: int,
    mod_err_str: Optional[str],
) -> None:
    if not func_name:
        func_name = "unknown function"

    if mod_err == libopenmpt.OPENMPT_ERROR_OUT_OF_MEMORY:  # type: ignore
        mod_err_str = libopenmpt.openmpt_error_string(mod_err)  # type: ignore
        if not mod_err_str:
            warnings.warn("Error: OPENMPT_ERROR_OUT_OF_MEMORY")
        else:
            warnings.warn(f"Error: {mod_err_str}")
            libopenmpt.openmpt_free_string(mod_err_str)  # type: ignore
    else:
        if not mod_err_str:
            mod_err_str = libopenmpt.openmpt_error_string(mod_err)  # type: ignore
            if not mod_err_str:
                warnings.warn(f"Error: {func_name} failed.")
            else:
                warnings.warn(f"Error: {func_name} failed: {mod_err_str}")
            libopenmpt.openmpt_free_string(mod_err_str)  # type: ignore


class PlayerBackendLibOpenMPT(PlayerBackend):
    def __init__(self, name: str = "LibOpenMPT") -> None:
        super().__init__(name)
        logger.debug("PlayerBackendLibOpenMPT initialized")

        self.openmpt_log_func = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
        )
        self.openmpt_error_func = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
        )
        self.load_mod = libopenmpt.openmpt_module_create_from_memory2  # type: ignore

    def check_module(self) -> bool:
        if not self.song:
            return False

        # ctls = ctypes.c_void_p()
        error = ctypes.c_int()
        error_message = ctypes.c_char_p()

        self.module_data = open(self.song.file_path, "rb").read()
        self.module_size = len(self.module_data)

        # Check if this extention is supported
        extension = self.song.file_path.split(".")[-1].lower().encode()
        if libopenmpt.openmpt_is_extension_supported(extension) == 0:  # type: ignore
            logger.warning(
                f"LibOpenMPT does not support the extension {extension.decode()}"
            )
            return False

        result = libopenmpt.openmpt_probe_file_header(  # type: ignore
            libopenmpt.OPENMPT_PROBE_FILE_HEADER_FLAGS_DEFAULT,  # int flags # type: ignore
            self.module_data,  # const void * filedata
            ctypes.c_size_t(self.module_size),  # size_t filesize
            self.module_size,  # size_t filesize
            self.openmpt_log_func(log_callback),  # openmpt_log_func logfunc
            None,  # void * loguser
            self.openmpt_error_func(error_callback),  # openmpt_error_func errfunc
            None,  # void * erruser
            ctypes.byref(error),  # int * error
            ctypes.byref(error_message),  # const char ** error_message
        )

        if result == libopenmpt.OPENMPT_PROBE_FILE_HEADER_RESULT_SUCCESS:  # type: ignore
            logger.debug("File will most likely be supported by libopenmpt.")
        elif result == libopenmpt.OPENMPT_PROBE_FILE_HEADER_RESULT_FAILURE:  # type: ignore
            logger.warning("File is not supported by libopenmpt.")
            return False
        elif result == libopenmpt.OPENMPT_PROBE_FILE_HEADER_RESULT_WANTMOREDATA:  # type: ignore
            logger.warning(
                "An answer could not be determined with the amount of data provided."
            )
            return False
        elif result == libopenmpt.OPENMPT_PROBE_FILE_HEADER_RESULT_ERROR:  # type: ignore
            logger.error("An internal error occurred.")
            print_error(
                "openmpt_probe_file_header()",
                error.value,
                ctypes.cast(
                    error_message, ctypes.POINTER(ctypes.c_char)
                ).contents.value.decode(),
            )
            libopenmpt.openmpt_free_string(error_message)  # type: ignore
            return False

        if not self.load_module():
            return False

        return True

    def load_module(self) -> bool:
        if not self.song:
            return False

        ctls = ctypes.c_void_p()
        error = ctypes.c_int()
        error_message = ctypes.c_char_p()

        self.module_data = open(self.song.file_path, "rb").read()
        self.module_size = len(self.module_data)

        self.mod = self.load_mod(  # type: ignore
            self.module_data,  # const void * filedata
            self.module_size,  # size_t filesize
            self.openmpt_log_func(log_callback),  # openmpt_log_func logfunc
            None,  # void * loguser
            self.openmpt_error_func(error_callback),  # openmpt_error_func errfunc
            None,  # void * erruser
            ctypes.byref(error),  # int * error
            ctypes.byref(error_message),  # const char ** error_message
            ctls,  # const openmpt_module_initial_ctl * ctls
        )

        if not self.mod:  # type: ignore
            logger.error(f"LibOpenMPT is unable to load {self.song.file_path}")
            print_error(
                "openmpt_module_create_from_memory2()",
                error.value,
                ctypes.cast(
                    error_message, ctypes.POINTER(ctypes.c_char)
                ).contents.value.decode(),
            )
            libopenmpt.openmpt_free_string(error_message)  # type: ignore
            return False
        return True

    def prepare_playing(self, subsong_nr: int = -1) -> None:
        if subsong_nr > -1:
            libopenmpt.openmpt_module_select_subsong(self.mod, subsong_nr)  # type: ignore
            name = libopenmpt.openmpt_module_get_subsong_name(self.mod, subsong_nr)  # type: ignore

            if isinstance(name, bytes):
                self.notify_song_name_changed(name.decode("iso-8859-1", "cp1252"))

    def get_module_length(self) -> int:
        self.load_module()
        duration_seconds = libopenmpt.openmpt_module_get_duration_seconds(self.mod)  # type: ignore
        return int(duration_seconds * 1000)  # type: ignore

    def read_chunk(self, samplerate: int, buffersize: int) -> Tuple[int, bytes]:
        libopenmpt.openmpt_module_error_clear(self.mod)  # type: ignore
        buffer = (ctypes.c_short * (buffersize * 2))()
        frame_count = libopenmpt.openmpt_module_read_interleaved_stereo(  # type: ignore
            self.mod, samplerate, buffersize, buffer
        )
        mod_err = libopenmpt.openmpt_module_error_get_last(self.mod)  # type: ignore
        mod_err_str = libopenmpt.openmpt_module_error_get_last_message(self.mod)  # type: ignore
        if mod_err != libopenmpt.OPENMPT_ERROR_OK:  # type: ignore
            logger.error("Error reading module: {}", mod_err_str)
            print_error(
                "openmpt_module_read_interleaved_stereo()",
                mod_err,  # type: ignore
                mod_err_str,  # type: ignore
            )
            libopenmpt.openmpt_free_string(mod_err_str)  # type: ignore
        return frame_count, bytes(buffer)  # type: ignore

    def get_position_seconds(self) -> float:
        return libopenmpt.openmpt_module_get_position_seconds(self.mod)  # type: ignore

    def get_module_title(self) -> Optional[str]:
        return libopenmpt.openmpt_module_get_metadata(self.mod, b"title")  # type: ignore

    def retrieve_song_info(self) -> None:
        if not self.song:
            return

        keys: List[str] = (  # type: ignore
            libopenmpt.openmpt_module_get_metadata_keys(self.mod)  # type: ignore
            .decode("iso-8859-1", "cp1252")
            .split(";")
        )
        for key in keys:  # type: ignore
            if isinstance(key, bytes):
                key = key.decode("iso-8859-1", "cp1252")
                key_c_char_p = ctypes.c_char_p(key.encode("iso-8859-1", "cp1252"))
                value = libopenmpt.openmpt_module_get_metadata(  # type: ignore
                    self.mod, key_c_char_p
                ).decode("iso-8859-1", "cp1252")
                if value != "":
                    match key:
                        case "type":
                            self.song.custom_metadata["type"] = value
                        case "type_long":
                            self.song.custom_metadata["type_long"] = value
                        case "originaltype":
                            self.song.custom_metadata["originaltype"] = value
                        case "originaltype_long":
                            self.song.custom_metadata["originaltype_long"] = value
                        case "container":
                            self.song.custom_metadata["container"] = value
                        case "container_long":
                            self.song.custom_metadata["container_long"] = value
                        case "tracker":
                            self.song.custom_metadata["tracker"] = value
                        case "artist":
                            self.song.artist = value
                        case "title":
                            self.song.title = value
                        case "date":
                            self.song.custom_metadata["date"] = value
                        case "message":
                            self.song.custom_metadata["message"] = value
                        case "message_raw":
                            self.song.custom_metadata["message_raw"] = value
                        case "warnings":
                            self.song.custom_metadata["warnings"] = value
                        case _:
                            pass

        self.song.subsongs = libopenmpt.openmpt_module_get_num_subsongs(self.mod)  # type: ignore
        self.song.duration = int(self.get_module_length())

        self.calculate_checksums()

    def free_module(self) -> None:
        if self.mod:
            libopenmpt.openmpt_module_destroy(self.mod)  # type: ignore
            self.mod = None

    def seek(self, position: int) -> None:
        libopenmpt.openmpt_module_set_position_seconds(self.mod, position)  # type: ignore
        logger.debug("Seeked to position: {}", position)

    def cleanup(self) -> None:
        self.free_module()
        logger.debug("PlayerBackendLibOpenMPT cleaned up")
