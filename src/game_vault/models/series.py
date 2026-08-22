from enum import StrEnum

from pydantic import BaseModel


class SeriesRole(StrEnum):
    MAINLINE = "mainline"
    SPIN_OFF = "spin_off"
    REMAKE = "remake"
    REMASTER = "remaster"
    EXPANSION = "expansion"
    OTHER = "other"


class GameSeries(BaseModel):
    id: str
    name: str


class GameSeriesMembership(BaseModel):
    game_id: str
    series_id: str
    role: SeriesRole
    sequence_number: int | None = None
