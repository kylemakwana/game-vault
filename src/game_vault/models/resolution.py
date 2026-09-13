"""Models used when resolving source data to Game Vault catalogue records."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ResolutionStatusEnum(StrEnum):
    """Possible outcomes when resolving a game release."""

    MATCHED = "matched"
    UNMATCHED = "unmatched"
    AMBIGUOUS = "ambiguous"


class MatchMethodEnum(StrEnum):
    """Methods used to resolve a candidate."""

    SOURCE_MAPPING = "source_mapping"
    EXTERNAL_IDENTIFIER = "external_identifier"
    TITLE_PLATFORM = "title_platform"
    MANUAL = "manual"


class ResolutionResult(BaseModel):
    """Result of attempting to resolve a candidate game release."""

    status: ResolutionStatusEnum

    game_release_id: str | None = None
    match_method: MatchMethodEnum | None = None
    confidence: float | None = None

    candidate_release_ids: list[str] = Field(default_factory=list)
    matched_values: list[str] = Field(default_factory=list)
