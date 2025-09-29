import json
import os
from importlib.resources import files
from typing import Any, Dict, Optional

from appdirs import user_config_dir


class Settings:
    def __init__(
        self, filename: str, path: str, app_name: str = "", anchor: str = "data"
    ) -> None:
        self.settings: Dict[str, Any] = {}
        self.name = filename
        self.path = path
        self.anchor = anchor
        self.folder_name = app_name

    def set(self, key: str, value: Any) -> None:
        self.settings[key] = value

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self.settings.get(key, default)

    def load(self) -> None:
        self.settings = {}

        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                json_data = json.load(f)
                if isinstance(json_data, Dict):
                    self.settings.update(json_data)  # type: ignore
                print(f"User settings loaded from {os.path.abspath(self.file_path)}")

    def save(self) -> None:
        file_path = os.path.join(self.path, f"{self.name}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(self.settings, f, indent=4)
        print(f"Settings saved to {file_path}")

    def to_dict(self) -> Dict[str, Any]:
        return self.settings

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        settings = cls(data.get("name", ""), data.get("path", ""))
        settings.settings = data
        return settings

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Settings):
            return False
        return self.settings == other.settings

    def ensure_default_config(self) -> None:
        config_dir = os.path.join(user_config_dir(), self.folder_name)
        os.makedirs(config_dir, exist_ok=True)

        default_config_path = files("data").joinpath(f"default_{self.name}.json")
        user_config_path = os.path.join(config_dir, f"{self.name}.json")

        if not os.path.exists(user_config_path):
            with (
                default_config_path.open("r") as src,
                open(user_config_path, "w") as dst,
            ):
                dst.write(src.read())
            print(f"Default configuration copied to {user_config_path}")

        self.path = config_dir
        self.file_path = user_config_path
