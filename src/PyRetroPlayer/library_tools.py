import argparse

from playlist.song_library import SongLibrary  # type: ignore


def clear_library(db_path: str):
    with SongLibrary(db_path) as library:
        library.clear()
        print("Library cleared.")


def main(db_path: str):
    with SongLibrary(db_path) as library:
        songs = library.get_all_songs()
        if not songs:
            print("No songs found in the library.")
            return
        for song in songs:
            print(f"ID: {song.id}")
            print(f"Title: {song.title}")
            print(f"Artist: {song.artist}")
            print(f"Album: {getattr(song, 'album', 'N/A')}")
            print(f"Duration: {song.duration}")
            print(f"File: {song.file_path}")
            print(f"Backend: {song.backend_name}")
            print(f"MD5: {song.md5}")
            print(f"SHA1: {song.sha1}")
            print(f"Custom Metadata: {song.custom_metadata}")
            print("-" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Song library tools")
    parser.add_argument("db_path", help="Path to the song library database")
    parser.add_argument("--clear", action="store_true", help="Clear the song library")
    args = parser.parse_args()

    if args.clear:
        clear_library(args.db_path)
    else:
        main(args.db_path)
