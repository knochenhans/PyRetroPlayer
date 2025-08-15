import json
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Song:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = ""
    title: str = ""
    artist: str = ""

    def __init__(
        self,
        id: Optional[str] = None,
        file_path: str = "",
        title: str = "",
        artist: str = "",
        backend_name: Optional[str] = None,
        duration: Optional[int] = None,
        md5: Optional[str] = None,
        sha1: Optional[str] = None,
        custom_metadata: Optional[dict] = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.file_path = file_path
        self.title = title
        self.artist = artist
        self.backend_name: Optional[str] = backend_name
        self.duration: Optional[int] = duration
        self.md5: Optional[str] = md5
        self.sha1: Optional[str] = sha1
        self.custom_metadata: Optional[dict] = custom_metadata
        self.is_ready: bool = False

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    @classmethod
    def from_json(cls, json_str: str) -> "Song":
        data = json.loads(json_str)
        return cls(**data)
