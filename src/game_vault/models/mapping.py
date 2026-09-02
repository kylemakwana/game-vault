"""Define mappings from external sources to catalogue releases."""

from pydantic import BaseModel


class SourceGameMapping(BaseModel):
    """Map a source-specific identifier to a game release."""

    source: str
    source_id: str

    game_release_id: str

    match_method: str
    confidence: float | None = None
