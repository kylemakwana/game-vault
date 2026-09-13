"""Define gaming platforms, services, identifiers, and accounts."""

from pydantic import BaseModel

from game_vault.config import IdentifierTypeEnum, PlatformEnum


class Platform(BaseModel):
    """Represent a hardware or software gaming platform."""

    id: str

    name: str
    ecosystem: str

    manufacturer: str | None = None


class GameService(BaseModel):
    """Represent an online gaming service."""

    id: str
    name: str


class ExternalIdentifier(BaseModel):
    """Identify a release within an external service."""

    service: PlatformEnum
    identifier_type: IdentifierTypeEnum
    value: str


class PlatformAccount(BaseModel):
    """Represent a user's account on a gaming service."""

    service_id: PlatformEnum

    username: str
    external_account_id: str

    avatar_url: str | None = None
