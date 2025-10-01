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
        self.conn.row_factory = sqlite3.Row
        with self.conn as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS songs (
                    id TEXT PRIMARY KEY,
                    file_path TEXT,
                    title TEXT,
                    artist TEXT,
                    duration INTEGER,
                    available_backends TEXT,
                    md5 TEXT,
                    sha1 TEXT,
                    custom_metadata TEXT
                )
                """
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_songs_file_path ON songs(file_path)"
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_songs_md5_sha1 ON songs(md5, sha1)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_songs_artist ON songs(artist)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_songs_title ON songs(title)")

        logger.info(f"Initialized SongLibrary with database at {db_path}")

        # Print all existing songs in the library
        all_songs = self.get_all_songs()
        logger.debug(f"Existing songs in library: {[song.title for song in all_songs]}")

    def add_song(self, song: Song) -> str:
        with self.conn as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM songs WHERE file_path = ?", (song.file_path,))
            row = cur.fetchone()
            if row:
                logger.info(
                    f"Song already exists: {song.file_path} (ID: {row['id']}). Not adding duplicate."
                )
                return row["id"]

            cur.execute(
                """
                INSERT INTO songs (
                    id, file_path, title, artist, duration, available_backends, md5, sha1, custom_metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    song.id,
                    song.file_path,
                    song.title,
                    song.artist,
                    song.duration,
                    json.dumps(song.available_backends),  # Serialize as JSON list
                    song.md5,
                    song.sha1,
                    json.dumps(
                        song.custom_metadata
                    ),  # Serialize custom metadata as JSON
                ),
            )
            logger.info(f"Added song: {song.title} to library with ID: {song.id}")
            return song.id

    def remove_song(self, song_id: str) -> None:
        with self.conn as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM songs WHERE id = ?", (song_id,))
            logger.info(f"Removed song with ID from library: {song_id}")

    def get_song(self, song_id: str) -> Optional[Song]:
        with self.conn as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
            row = cur.fetchone()
            if row:
                return Song(
                    id=row["id"],
                    file_path=row["file_path"],
                    title=row["title"],
                    artist=row["artist"],
                    duration=row["duration"],
                    available_backends=json.loads(row["available_backends"]) if row["available_backends"] else [],
                    md5=row["md5"],
                    sha1=row["sha1"],
                    custom_metadata=(
                        json.loads(row["custom_metadata"])
                        if row["custom_metadata"]
                        else {}
                    ),  # Deserialize JSON
                )
            return None

    def get_songs(self, song_ids: List[str]) -> List[Song]:
        if not song_ids:
            return []
        placeholders = ",".join("?" for _ in song_ids)
        query = f"SELECT * FROM songs WHERE id IN ({placeholders})"
        with self.conn as conn:
            cur = conn.cursor()
            cur.execute(query, song_ids)
            rows = cur.fetchall()
            song_map = {
                row["id"]: Song(
                    id=row["id"],
                    file_path=row["file_path"],
                    title=row["title"],
                    artist=row["artist"],
                    duration=row["duration"],
                    available_backends=json.loads(row["available_backends"]) if row["available_backends"] else [],
                    md5=row["md5"],
                    sha1=row["sha1"],
                    custom_metadata=(
                        json.loads(row["custom_metadata"])
                        if row["custom_metadata"]
                        else {}
                    ),
                )
                for row in rows
            }
            return [song_map[sid] for sid in song_ids if sid in song_map]

    def get_all_songs(self) -> List[Song]:
        with self.conn as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM songs")
            return [
                Song(
                    id=row["id"],
                    file_path=row["file_path"],
                    title=row["title"],
                    artist=row["artist"],
                    duration=row["duration"],
                    available_backends=json.loads(row["available_backends"]) if row["available_backends"] else [],
                    md5=row["md5"],
                    sha1=row["sha1"],
                    custom_metadata=(
                        json.loads(row["custom_metadata"])
                        if row["custom_metadata"]
                        else {}
                    ),  # Deserialize JSON
                )
                for row in cur.fetchall()
            ]

    def check_song_exists(self, song_id: str) -> bool:
        with self.conn as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM songs WHERE id = ?", (song_id,))
            return cur.fetchone() is not None

    def remove_missing_files(self) -> None:
        with self.conn as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, file_path FROM songs")
            rows = cur.fetchall()
            for row in rows:
                song_id, file_path = row["id"], row["file_path"]
                if not os.path.exists(file_path):
                    logger.warning(f"Removing missing file: {file_path}")
                    self.remove_song(song_id)

    def clear(self) -> None:
        with self.conn as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM songs")
            logger.debug("Cleared song library")

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "SongLibrary":
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()
