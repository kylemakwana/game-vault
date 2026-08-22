from pydantic import BaseModel


class SourceGameMapping(BaseModel):
    source: str
    source_id: str

    game_release_id: str

    match_method: str
    confidence: float | None = None
