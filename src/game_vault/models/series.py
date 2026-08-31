"""Define game-series models and membership roles."""

from enum import StrEnum

from pydantic import BaseModel


class SeriesRole(StrEnum):
    """Describe how a game participates in a series."""

    MAINLINE = "mainline"
    SPIN_OFF = "spin_off"
    REMAKE = "remake"
    REMASTER = "remaster"
    EXPANSION = "expansion"
    OTHER = "other"


class GameSeries(BaseModel):
    """Represent a named series of related games."""

    id: str
    name: str


class GameSeriesMembership(BaseModel):
    """Associate a game with a series and its role within that series."""

    game_id: str
    series_id: str
    role: SeriesRole
    sequence_number: int | None = None
