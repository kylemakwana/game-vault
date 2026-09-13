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
    PSVITA = "PSVITA"
    UNKNOWN = "Unknown PlayStation console"


class PlayStationTitleCategoryEnum(StrEnum):
    """Mapped PlayStation Console enum."""

    PS5_NATIVE_GAME = "ps5_native_game"
    PS4_GAME = "ps4_game"
    UNKNOWN = "unknown"


class PlayStationSourceTypeEnum(StrEnum):
    """PlayStation soruce type enum."""

    PLAYED_TITLE = "Played Title"
    TROPHY_TITLE = "Trophy Title"


class IdentifierTypeEnum(StrEnum):
    TITLE_ID = "TITLE_ID"
    NP_COMMUNICATION_ID = "NP_COMMUNICATION_ID"
    NP_TITLE_ID = "NP_TITLE_ID"


class SourceTypeMappingEnum(StrEnum):
    """Source type mapping."""

    PLAYSTATION_TITLE = "playstation_title"
    PLAYSTATION_TROPHY_SET = "playstation_trophy_set"
