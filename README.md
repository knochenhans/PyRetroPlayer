<img width="1238" height="725" alt="grafik" src="https://github.com/user-attachments/assets/acbf64bf-ae0b-417a-a199-8cd8d73701f4" />

Retro music player application inspired by foobar2000, using `libopenmpt` and `libuade` to play module files, and also supports `libgme`. This application is built with Python and PySide6 for the GUI, and uses `pyaudio` for audio playback. It chooses the best player based on the module type. Has some basic features to connect with *[The Mod Archive](https://modarchive.org)* for looking up songs, scraping metadata and download your favorites via user ID.

Uses [libopenmpt_py](https://github.com/shroom00/libopenmpt_py) to interface with `libopenmpt` via Python.

Only works under Linux for now.

Based on my older projects [Mod Archive Random Player](https://github.com/knochenhans/modarchive-random-player) and [PyUADE](https://github.com/knochenhans/pyuade).

## Features

- Typical playback features like Play, Pause, and Stop.
- Load and play random module files from *The Mod Archive*, download your favourites or download modules by artist.
- Allows looking up the current module on *The Mod Archive* (including metadata scraping) and *.mod Sample Master*.
- Display module meta data.
- System tray notifications for the currently playing module.
- Progress slider to show the current playback position.
- Tray icon to show/hide the main window, also provides play/pause/stop controls.
- Multi-tab interface.
- Uses SQLite for save mod informations.
- Basic MPRIS support for media player controls via media keys or desktop environment media controls.

## How to use

- Enter Member ID in the settings if you want to load random files from a member's favourites.
- Click on the tray icon to show/hide the main window, or press Escape to hide it.
