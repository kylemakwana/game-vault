import json

import pytest
from pydantic import BaseModel, ValidationError

from game_vault.loaders.catalog_loader import load_catalog


class DummyModel(BaseModel):
    id: str
    name: str


def test_load_catalog(tmp_path):
    data = [
        {"id": "minecraft", "name": "Minecraft"},
        {"id": "witcher-3", "name": "The Witcher 3"},
    ]

    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(data), encoding="utf-8")

    result = load_catalog(catalog_path, DummyModel)

    assert result == [
        DummyModel(id="minecraft", name="Minecraft"),
        DummyModel(id="witcher-3", name="The Witcher 3"),
    ]


def test_load_catalog_returns_empty_list_for_empty_catalog(tmp_path):
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text("[]", encoding="utf-8")

    result = load_catalog(catalog_path, DummyModel)

    assert result == []


def test_load_catalog_raises_validation_error_for_invalid_data(tmp_path):
    data = [
        {"id": "minecraft"},
    ]

    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_catalog(catalog_path, DummyModel)
