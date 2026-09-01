"""Load environment-backed configuration for Game Vault."""

import os
from enum import StrEnum

from dotenv import load_dotenv

load_dotenv()

PSN_NPSSO = os.environ["PSN_NPSSO"]


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
