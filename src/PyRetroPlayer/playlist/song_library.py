import json
import os
import sqlite3
from types import TracebackType
from typing import List, Optional

from loguru import logger
from playlist.song import Song  # type: ignore


class SongLibrary:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS songs (
                id TEXT PRIMARY KEY,
                file_path TEXT,
                title TEXT,
                artist TEXT,
                album TEXT,
                duration INTEGER,
                backend_name TEXT,
                md5 TEXT,
                sha1 TEXT,
                custom_metadata TEXT
            )
        """
        )

        logger.info(f"Initialized SongLibrary with database at {db_path}")

        # Print all existing songs in the library
        all_songs = self.get_all_songs()
        logger.debug(f"Existing songs in library: {[song.title for song in all_songs]}")

    def add_song(self, song: Song) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO songs (
                id, file_path, title, artist, duration, backend_name, md5, sha1, custom_metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                song.id,
                song.file_path,
                song.title,
                song.artist,
                song.duration,
                song.backend_name,
                song.md5,
                song.sha1,
                json.dumps(song.custom_metadata),  # Serialize custom metadata as JSON
            ),
        )
        logger.info(f"Added or updated song: {song.title} by {song.artist}")
        self.conn.commit()

    def remove_song(self, song_id: str) -> None:
        self.conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        logger.info(f"Removed song with ID: {song_id}")
        self.conn.commit()

    def get_song(self, song_id: str) -> Optional[Song]:
        cursor = self.conn.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
        row = cursor.fetchone()
        if row:
            return Song(
                id=row[0],
                file_path=row[1],
                title=row[2],
                artist=row[3],
                duration=row[5],
                backend_name=row[6],
                md5=row[7],
                sha1=row[8],
                custom_metadata=(
                    json.loads(row[9]) if row[9] else {}
                ),  # Deserialize JSON
            )
        return None

    def get_all_songs(self) -> List[Song]:
        cursor = self.conn.execute("SELECT * FROM songs")
        return [
            Song(
                id=row[0],
                file_path=row[1],
                title=row[2],
                artist=row[3],
                duration=row[5],
                backend_name=row[6],
                md5=row[7],
                sha1=row[8],
                custom_metadata=(
                    json.loads(row[9]) if row[9] else {}
                ),  # Deserialize JSON
            )
            for row in cursor.fetchall()
        ]

    def check_song_exists(self, song_id: str) -> bool:
        cursor = self.conn.execute("SELECT 1 FROM songs WHERE id = ?", (song_id,))
        return cursor.fetchone() is not None

    def remove_missing_files(self) -> None:
        cursor = self.conn.execute("SELECT id, file_path FROM songs")
        rows = cursor.fetchall()
        for song_id, file_path in rows:
            if not os.path.exists(file_path):
                logger.warning(f"Removing missing file: {file_path}")
                self.remove_song(song_id)

    def clear(self) -> None:
        self.conn.execute("DELETE FROM songs")
        self.conn.commit()

        logger.debug("Cleared song library")

    def close(self) -> None:
        self.conn.close()

    def __del__(self) -> None:
        self.close()

    def __enter__(self) -> "SongLibrary":
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()
