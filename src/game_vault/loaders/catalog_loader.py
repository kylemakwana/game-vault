import json
from pathlib import Path

from game_vault.models.game import GameRelease
from game_vault.models.mapping import SourceGameMapping


def load_mappings(path: Path) -> list[SourceGameMapping]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return [SourceGameMapping.model_validate(item) for item in data]


def load_releases(path: Path) -> list[GameRelease]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return [GameRelease.model_validate(item) for item in data]
