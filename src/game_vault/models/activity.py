"""Define gameplay activity models."""

from datetime import datetime

from pydantic import BaseModel


class PlayActivity(BaseModel):
    """Represent an account's recorded activity for a game release."""

    account_id: str
    game_release_id: str

    playtime_seconds: int | None = None
    play_count: int | None = None

    first_played_at: datetime | None = None
    last_played_at: datetime | None = None

    source: str
