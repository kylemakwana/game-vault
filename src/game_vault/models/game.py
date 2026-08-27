from datetime import date

from pydantic import BaseModel, Field

from game_vault.models.platform import ExternalIdentifier


class Game(BaseModel):
    id: str

    name: str
    sort_name: str | None = None

    release_date: date | None = None

    developer: str | None = None
    publisher: str | None = None

    genres: list[str] = Field(default_factory=list)

    image_url: str | None = None


class GameRelease(BaseModel):
    id: str

    game_id: str
    platform_id: str

    name: str

    release_date: date | None = None

    image_url: str | None = None

    external_identifiers: list[ExternalIdentifier] = Field(default_factory=list)
