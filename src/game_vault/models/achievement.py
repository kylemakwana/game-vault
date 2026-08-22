from datetime import datetime

from pydantic import BaseModel, Field


class Achievement(BaseModel):
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
    id: str
    achievement_set_id: str
    external_group_id: str
    name: str | None = None


class AchievementSet(BaseModel):
    id: str
    game_release_id: str
    service_id: str
    name: str | None = None
    external_identifier: str | None = None
    groups: list[AchievementGroup] = Field(default_factory=list)


class AchievementProgress(BaseModel):
    achievemnt_id: str
    account_id: str
    unlocked: bool
    unlocked_at: datetime | None = None
    progress: int | None = None
    progress_percentage: int | None = None
    progresssed_at: datetime | None = None
