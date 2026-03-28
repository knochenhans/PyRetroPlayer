from typing import Any, Dict, List

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
        self.current_metadata: Dict[str, Any] = {}

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
                "Identity": "PyRetroPlayer",
                "SupportedUriSchemes": dbus.Array(["file"], signature="s"),  # type: ignore
                "SupportedMimeTypes": dbus.Array([], signature="s"),  # type: ignore
            }

        if interface_name == "org.mpris.MediaPlayer2.Player":
            if not self.player.has_media:
                status = "Stopped"
            elif self.player.playing:
                status = "Playing"
            else:
                status = "Paused"

            return {
                "PlaybackStatus": status,
                "CanPlay": self.player.has_media,
                "Metadata": self.get_metadata(),  # type: ignore
                "CanPause": True,
                "CanGoNext": True,
                "CanGoPrevious": True,
                "CanControl": True,
            }

        return {}

    @dbus.service.method("org.mpris.MediaPlayer2.Player")  # type: ignore
    def Play(self) -> None:
        self.player.external_play()
        self.update_playback()

    @dbus.service.method("org.mpris.MediaPlayer2.Player")  # type: ignore
    def Pause(self) -> None:
        self.player.pause()
        self.update_playback()

    @dbus.service.method("org.mpris.MediaPlayer2.Player")  # type: ignore
    def PlayPause(self) -> None:
        self.player.toggle()
        self.update_playback()

    @dbus.service.method("org.mpris.MediaPlayer2.Player")  # type: ignore
    def Stop(self) -> None:
        self.player.stop()
        self.update_playback()

    @dbus.service.method("org.mpris.MediaPlayer2.Player")  # type: ignore
    def Next(self) -> None:
        self.player.next()
        self.update_playback()

    @dbus.service.method("org.mpris.MediaPlayer2.Player")  # type: ignore
    def Previous(self) -> None:
        self.player.previous()
        self.update_playback()

    @dbus.service.signal("org.freedesktop.DBus.Properties", signature="sa{sv}as")  # type: ignore
    def PropertiesChanged(
        self, interface: str, changed: Dict[str, object], invalidated: List[str]
    ) -> None:
        pass

    def update_playback(self) -> None:
        playing_status = (
            "Playing"
            if self.player.playing
            else "Paused" if self.player.has_media else "Stopped"
        )

        self.PropertiesChanged(
            "org.mpris.MediaPlayer2.Player",
            {
                "PlaybackStatus": playing_status,
                "Metadata": self.get_metadata(),  # type: ignore
                "Position": dbus.Int64(0),  # type: ignore
            },
            [],
        )

    def get_metadata(self) -> dbus.Dictionary:  # type: ignore
        return dbus.Dictionary(  # type: ignore
            {
                "xesam:title": self.current_metadata.get("title", "Unknown Title"),
                "xesam:artist": dbus.Array(  # type: ignore
                    [self.current_metadata.get("artist", "Unknown Artist")],
                    signature="s",
                ),
            },
            signature="sv",
        )

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        self.current_metadata = metadata
        self.update_playback()
