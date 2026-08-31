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


class IdentifierType(StrEnum):
    """Identifier enum."""

    PLAYED_TITLE = "Played Title"
    TROPHY_TITLE = "Trophy Title"
