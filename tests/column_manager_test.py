import json
import os
from typing import Any, Dict, List

import pytest

from PyRetroPlayer.playlist.column_manager import ColumnManager


@pytest.fixture
def column_manager() -> ColumnManager:
    columns: List[Dict[str, Any]] = [
        {"id": "name", "name": "Name", "width": 100, "visible": True},
        {"id": "artist", "name": "Artist", "width": 150, "visible": True},
        {"id": "playing", "name": "Playing", "width": 50, "visible": False},
    ]
    return ColumnManager(columns)


def test_get_column_ids(column_manager: ColumnManager) -> None:
    assert column_manager.get_column_ids() == ["name", "artist", "playing"]


def test_get_column_name(column_manager: ColumnManager) -> None:
    assert column_manager.get_column_name("name") == "Name"
    assert column_manager.get_column_name("artist") == "Artist"


def test_get_column_names(column_manager: ColumnManager) -> None:
    assert column_manager.get_column_names() == ["Name", "Artist", "Playing"]


def test_get_column_width(column_manager: ColumnManager) -> None:
    assert column_manager.get_column_width("name") == 100
    assert column_manager.get_column_width("artist") == 150


def test_get_column_widths(column_manager: ColumnManager) -> None:
    assert column_manager.get_column_widths() == [100, 150]


def test_set_column_width(column_manager: ColumnManager) -> None:
    column_manager.set_column_width("name", 120)
    assert column_manager.get_column_width("name") == 120


def test_is_column_visible(column_manager: ColumnManager) -> None:
    assert column_manager.is_column_visible("name") is True
    assert column_manager.is_column_visible("playing") is False


def test_set_column_visibility(column_manager: ColumnManager) -> None:
    column_manager.set_column_visibility("playing", True)
    assert column_manager.is_column_visible("playing") is True


def test_set_column_order(column_manager: ColumnManager) -> None:
    new_order = ["playing", "artist", "name"]
    column_manager.set_column_order(new_order)
    assert column_manager.get_column_ids() == new_order


def test_set_column_order_invalid(column_manager: ColumnManager) -> None:
    with pytest.raises(ValueError):
        column_manager.set_column_order(["name", "artist"])


def test_save_to_json_and_load_from_json(column_manager: ColumnManager) -> None:
    file_path = "test_columns.json"
    column_manager.save_to_json(file_path)

    with open(file_path, "r") as file:
        data = json.load(file)
        assert data["order"] == ["name", "artist", "playing"]
        assert len(data["columns"]) == 3

    loaded_manager = ColumnManager.load_from_json(file_path)
    assert loaded_manager.get_column_ids() == ["name", "artist", "playing"]
    os.remove(file_path)
