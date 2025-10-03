import json
import uuid
from typing import Any, Dict, List, Optional


class Song:
    id: str
    file_path: str
    title: str
    artist: str
    available_backends: List[str]
    duration: Optional[int]
    md5: Optional[str]
    sha1: Optional[str]
    custom_metadata: Dict[str, Any]
    is_ready: bool

    def __init__(
        self,
        id: Optional[str] = None,
        file_path: str = "",
        title: str = "",
        artist: str = "",
        available_backends: Optional[List[str]] = None,
        duration: Optional[int] = None,
        md5: Optional[str] = None,
        sha1: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.file_path = file_path
        self.title = title
        self.artist = artist
        self.available_backends = available_backends or []
        self.duration = duration
        self.md5 = md5
        self.sha1 = sha1
        self.custom_metadata = custom_metadata or {}
        self.is_ready = False

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    @classmethod
    def from_json(cls, json_str: str) -> "Song":
        data: Dict[str, Any] = json.loads(json_str)
        return cls(**data)
