"""Define gaming platforms, services, identifiers, and accounts."""

from pydantic import BaseModel


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

    service: str
    identifier_type: str
    value: str


class PlatformAccount(BaseModel):
    """Represent a user's account on a gaming service."""

    id: str

    service_id: str

    username: str | None = None
    external_account_id: str | None = None

    avatar_url: str | None = None
