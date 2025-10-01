import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
        available_backends: Optional[List[str]] = None,
        duration: Optional[int] = None,
        md5: Optional[str] = None,
        sha1: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.file_path = file_path
        self.title = title
        self.artist = artist
        self.available_backends: List[str] = available_backends or []
        self.duration: Optional[int] = duration
        self.md5: Optional[str] = md5
        self.sha1: Optional[str] = sha1
        self.custom_metadata: Dict[str, Any] = custom_metadata or {}
        self.is_ready: bool = False

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    @classmethod
    def from_json(cls, json_str: str) -> "Song":
        data = json.loads(json_str)
        return cls(**data)
