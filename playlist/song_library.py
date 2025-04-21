from typing import List
from playlist.song import Song
import sqlite3


class SongLibrary:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS songs (
                id TEXT PRIMARY KEY,
                file_path TEXT,
                title TEXT,
                artist TEXT
            )
        """
        )

    def add_song(self, song: Song) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO songs (id, file_path, title, artist) 
            VALUES (?, ?, ?, ?)
            """,
            (song.id, song.file_path, song.title, song.artist),
        )
        self.conn.commit()

    def remove_song(self, song_id: str) -> None:
        self.conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        self.conn.commit()

    def get_song(self, song_id: str) -> Song | None:
        cursor = self.conn.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
        row = cursor.fetchone()
        if row:
            return Song(*row)
        return None

    def get_all_songs(self) -> List[Song]:
        cursor = self.conn.execute("SELECT * FROM songs")
        return [Song(*row) for row in cursor.fetchall()]

    def clear(self) -> None:
        self.conn.execute("DELETE FROM songs")
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __del__(self) -> None:
        self.close()

    def __enter__(self) -> "SongLibrary":
        return self
