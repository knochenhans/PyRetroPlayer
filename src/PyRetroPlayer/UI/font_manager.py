import shutil
import tempfile
from importlib.resources import as_file, files
from pathlib import Path
from typing import Set

from loguru import logger
from PySide6.QtCore import QDir
from PySide6.QtGui import QFontDatabase


class FontManager:
    def __init__(self) -> None:
        self.font_db: QFontDatabase = QFontDatabase()

        font_dir_traversable = files("PyRetroPlayer.fonts")

        self.font_dir = tempfile.mkdtemp()

        with as_file(font_dir_traversable) as font_path:
            Path(self.font_dir).mkdir(parents=True, exist_ok=True)
            font_path = Path(font_path)
            for font_file in font_path.glob("*.ttf"):
                shutil.copy(font_file, self.font_dir)

        self.setup_fonts()

    def __del__(self) -> None:
        shutil.rmtree(self.font_dir, ignore_errors=True)

    def load_fonts_from_dir(self, directory: str) -> Set[str]:
        families: Set[str] = set()
        dir_obj = QDir(directory)

        if not dir_obj.exists():
            logger.error(f"Font directory does not exist: {directory}")
            return families

        for file_info in dir_obj.entryInfoList(["*.ttf", "*.otf"]):
            font_path = file_info.absoluteFilePath()
            _id = QFontDatabase.addApplicationFont(font_path)
            if _id == -1:
                logger.warning(f"Failed to load font: {font_path}")
                continue
            loaded_families = set(QFontDatabase.applicationFontFamilies(_id))
            logger.debug(f"Loaded font(s): {loaded_families}")
            families |= loaded_families

        return families

    def setup_fonts(self) -> None:
        families = self.load_fonts_from_dir(self.font_dir)
        if not families:
            logger.warning("No fonts loaded from font directory.")
        else:
            logger.debug(f"Available font families: {families}")