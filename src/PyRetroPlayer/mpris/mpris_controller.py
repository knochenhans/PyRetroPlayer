from typing import Any, Dict

import dbus  # type: ignore
import dbus.service  # type: ignore

from PyRetroPlayer.mpris.mpris_controller_core import MPRISControllerCore

BUS_NAME: str = "org.mpris.MediaPlayer2.PyRetroPlayer"
OBJECT_PATH: str = "/org/mpris/MediaPlayer2"


class MPRISPlayer(dbus.service.Object):
    def __init__(self, player: "MPRISControllerCore") -> None:
        bus: dbus.SessionBus = dbus.SessionBus()
        name: dbus.service.BusName = dbus.service.BusName(BUS_NAME, bus)  # type: ignore

        super().__init__(name, OBJECT_PATH)  # type: ignore

        self.player: MPRISControllerCore = player

    @dbus.service.method(  # type: ignore
        "org.freedesktop.DBus.Properties",
        in_signature="ss",
        out_signature="v",
    )
    def Get(self, interface_name: str, property_name: str) -> Any:
        return self.GetAll(interface_name)[property_name]

    @dbus.service.method(  # type: ignore
        "org.freedesktop.DBus.Properties",
        in_signature="s",
        out_signature="a{sv}",
    )
    def GetAll(self, interface_name: str) -> Dict[str, Any]:
        if interface_name == "org.mpris.MediaPlayer2":
            return {
                "CanQuit": True,
                "CanRaise": False,
                "HasTrackList": False,
                "Identity": "Qt Test Player",
                "SupportedUriSchemes": dbus.Array(["file"], signature="s"),  # type: ignore
                "SupportedMimeTypes": dbus.Array([], signature="s"),  # type: ignore
            }

        if interface_name == "org.mpris.MediaPlayer2.Player":
            metadata = dbus.Dictionary(
                {
                    "xesam:title": "Test Song",
                    "xesam:artist": dbus.Array(["Test Artist"], signature="s"),
                },
                signature="sv",
            )
            return {
                "PlaybackStatus": "Playing" if self.player.playing else "Paused",
                "Metadata": metadata,
                "CanPlay": True,
                "CanPause": True,
                "CanGoNext": True,
                "CanGoPrevious": True,
                "CanControl": True,
            }

        return {}

    @dbus.service.method("org.mpris.MediaPlayer2.Player")  # type: ignore
    def Play(self) -> None:
        self.player.play()
        self._update_playback()

    @dbus.service.method("org.mpris.MediaPlayer2.Player")  # type: ignore
    def Pause(self) -> None:
        self.player.pause()
        self._update_playback()

    @dbus.service.method("org.mpris.MediaPlayer2.Player")  # type: ignore
    def PlayPause(self) -> None:
        self.player.toggle()
        self._update_playback()

    @dbus.service.method("org.mpris.MediaPlayer2.Player")  # type: ignore
    def Next(self) -> None:
        self.player.next()
        self._update_playback()

    @dbus.service.method("org.mpris.MediaPlayer2.Player")  # type: ignore
    def Previous(self) -> None:
        self.player.previous()
        self._update_playback()

    @dbus.service.signal("org.freedesktop.DBus.Properties", signature="sa{sv}as")  # type: ignore
    def PropertiesChanged(
        self, interface: str, changed: dict[str, object], invalidated: list[str]
    ) -> None:
        pass

    def _update_playback(self) -> None:
        self.PropertiesChanged(
            "org.mpris.MediaPlayer2.Player",
            {"PlaybackStatus": "Playing" if self.player.playing else "Paused"},
            [],
        )
