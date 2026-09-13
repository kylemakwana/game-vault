"""Define shared configuration values for Game Vault."""

from enum import StrEnum


class PlatformEnum(StrEnum):
    """Platform enum."""

    PLAYSTATION = "PlayStation"
    STEAM = "Steam"


class PlayStationPlatformEnum(StrEnum):
    """PlayStation Console enum."""

    PS5 = "PS5"
    PS4 = "PS4"
    PS3 = "PS3"
    PSPC = "PSPC"
    UNKNOWN = "Unknown PlayStation console"


class PlayStationTitleCategoryEnum(StrEnum):
    """Mapped PlayStation Console enum."""

    PS5_NATIVE_GAME = "ps5_native_game"
    PS4_GAME = "ps4_game"
    UNKNOWN = "unknown"


class IdentifierTypeEnum(StrEnum):
    """Identifier enum."""

    PLAYED_TITLE = "Played Title"
    TROPHY_TITLE = "Trophy Title"
