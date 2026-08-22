from pydantic import BaseModel


class Platform(BaseModel):
    id: str

    name: str
    ecosystem: str

    manufacturer: str | None = None


class GameService(BaseModel):
    id: str
    name: str


class ExternalIdentifier(BaseModel):
    service: str
    identifier_type: str
    value: str


class PlatformAccount(BaseModel):
    id: str

    service_id: str

    username: str | None = None
    external_account_id: str | None = None

    avatar_url: str | None = None
