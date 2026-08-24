import json
from pathlib import Path

from game_vault.models.game import Game, GameRelease
from game_vault.models.mapping import SourceGameMapping
from game_vault.models.series import GameSeries, GameSeriesMembership


def load_mappings(path: Path) -> list[SourceGameMapping]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return [SourceGameMapping.model_validate(item) for item in data]


def load_releases(path: Path) -> list[GameRelease]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return [GameRelease.model_validate(item) for item in data]


def load_games(path: Path) -> list[Game]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return [Game.model_validate(item) for item in data]


def load_series(path: Path) -> list[GameSeries]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return [GameSeries.model_validate(item) for item in data]


def load_series_memberships(path: Path) -> list[GameSeriesMembership]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return [GameSeriesMembership.model_validate(item) for item in data]
