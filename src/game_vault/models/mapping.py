"""Define mappings from external sources to catalogue releases."""

from pydantic import BaseModel

from game_vault.models.resolution import MatchMethodEnum


class SourceGameMapping(BaseModel):
    """Map a source-specific identifier to a game release."""

    source: str
    source_id: str

    game_release_id: str

    match_method: MatchMethodEnum
    confidence: float | None = None
