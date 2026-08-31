"""Define normalized models for PlayStation snapshot data."""

from datetime import datetime

from pydantic import BaseModel, Field


class TrophyCounts(BaseModel):
    """Store trophy counts by PlayStation trophy type."""

    bronze: int = 0
    silver: int = 0
    gold: int = 0
    platinum: int = 0

    @property
    def total(self) -> int:
        """Return the total number of trophies across all types.

        :return: Sum of bronze, silver, gold, and platinum trophies.
        """
        return self.bronze + self.silver + self.gold + self.platinum


class SnapshotMetadata(BaseModel):
    """Describe the source, schema, and creation time of a snapshot."""

    source: str = "playstation"
    schema_version: str = "0.1.0"
    generated_at: datetime


class PlayStationAccount(BaseModel):
    """Represent the PlayStation account captured by a snapshot."""

    online_id: str
    account_id: str
    np_id: str | None = None
    languages: list[str] = Field(default_factory=list)
    avatar_url: str | None = None


class TrophySummary(BaseModel):
    """Summarize an account's trophy level and earned trophies."""

    level: int
    level_progress: int
    earned: TrophyCounts


class DeviceActivation(BaseModel):
    """Represent one activation of a PlayStation device."""

    activation_type: str
    activation_date: datetime


class PlayStationDevice(BaseModel):
    """Represent a PlayStation device and its account activations."""

    device_id: str
    device_name: str | None = None
    device_type: str
    account_device_vector: str | None = None
    activations: list[DeviceActivation] = Field(default_factory=list)


class PlayedTitle(BaseModel):
    """Represent a title in the account's PlayStation play history."""

    title_id: str
    name: str
    image_url: str | None = None

    reported_category: str
    content_type: str
    classification_source: str

    play_count: int
    play_duration_seconds: int

    first_played_at: datetime | None = None
    last_played_at: datetime | None = None


class UserTrophyProgress(BaseModel):
    """Represent account-specific progress for a trophy."""

    earned: bool

    earned_at: datetime | None = None

    progress: int | None = None
    progress_rate: int | None = None
    progressed_at: datetime | None = None


class Trophy(BaseModel):
    """Represent a PlayStation trophy and the user's progress toward it."""

    trophy_id: int
    trophy_set_version: str

    name: str
    detail: str | None = None

    type: str
    hidden: bool

    icon_url: str | None = None

    rarity: str | None = None
    earn_rate: float | None = None

    progress_target_value: int | None = None
    reward_name: str | None = None
    reward_image_url: str | None = None

    user_progress: UserTrophyProgress


class PlaystationTrophyGroup(BaseModel):
    """Group trophies within a PlayStation trophy set."""

    group_id: str
    name: str | None = None
    trophies: list[Trophy] = Field(default_factory=list)


class PlaystationTrophyTitle(BaseModel):
    """Represent a PlayStation title and its complete trophy set."""

    np_communication_id: str
    np_service_name: str
    np_title_id: str | None = None

    trophy_set_version: str

    title_name: str
    title_detail: str | None = None
    title_icon_url: str | None = None

    platforms: list[str]

    has_trophy_groups: bool
    hidden: bool
    progress: int

    earned_trophies: TrophyCounts
    defined_trophies: TrophyCounts

    last_updated_at: datetime | None = None

    groups: list[PlaystationTrophyGroup] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Describe the completeness and consistency of imported snapshot data."""

    trophy_title_summary_complete: bool
    trophy_detail_import_complete: bool

    expected_trophy_titles_count: int
    imported_trophy_titles_count: int

    expected_trophy_detail_sets_count: int
    imported_trophy_detail_sets_count: int

    profile_trophy_totals: TrophyCounts
    imported_trophy_totals: TrophyCounts

    trophy_totals_match: bool

    warnings: list[str] = Field(default_factory=list)


class PlayStationSnapshot(BaseModel):
    """Aggregate normalized account, activity, device, and trophy data."""

    snapshot: SnapshotMetadata

    account: PlayStationAccount
    trophy_summary: TrophySummary

    devices: list[PlayStationDevice]
    played_titles: list[PlayedTitle]
    trophy_titles: list[PlaystationTrophyTitle]

    validation: ValidationResult
