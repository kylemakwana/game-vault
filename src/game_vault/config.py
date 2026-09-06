"""Define shared configuration values for Game Vault."""

from enum import StrEnum


class Platform(StrEnum):
    """Platform enum."""

    PLAYSTATION = "PlayStation"
    STEAM = "Steam"


class PlayStationConsole(StrEnum):
    """PlayStation Console enum."""

    PS5 = "PS5"
    PS4 = "PS4"
    PS3 = "PS3"
    PS_UNKNOWN = "Unknown PlayStation console"


class IdentifierType(StrEnum):
    """Identifier enum."""

    PLAYED_TITLE = "Played Title"
    TROPHY_TITLE = "Trophy Title"
