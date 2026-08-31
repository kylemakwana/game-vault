"""Define achievement and achievement-progress models."""

from datetime import datetime

from pydantic import BaseModel


class Achievement(BaseModel):
    """Represent an achievement exposed by a gaming service."""

    id: str
    achievement_set_id: str
    group_id: str
    external_id: str
    name: str
    description: str | None = None
    icon_url: str | None = None
    hidden: bool = False
    achievement_type: str | None = None
    rarity: str | None = None
    global_unlock_percentage: float | None = None
    progress_target: int | None = None


class AchievementGroup(BaseModel):
    """Group related achievements within an achievement set."""

    id: str
    achievement_set_id: str
    external_group_id: str
    name: str | None = None


class AchievementSet(BaseModel):
    """Represent a service-specific achievement set for a game release."""

    id: str
    game_release_id: str
    service_id: str
    name: str | None = None
    external_identifier: str | None = None


class AchievementProgress(BaseModel):
    """Record an account's progress toward an achievement."""

    achievement_id: str
    account_id: str
    unlocked: bool
    unlocked_at: datetime | None = None
    progress: int | None = None
    progress_percentage: int | None = None
    progressed_at: datetime | None = None
