from dataclasses import dataclass
from enum import Enum, unique
from typing import List
from uuid import UUID


@unique
class Role(Enum):
    STAFF = 1
    SUPERUSER = 2
    USER = 3
    PILOT = 4


@dataclass
class Client:
    uid: UUID
    name: str


@dataclass
class GCPUser:
    """Maps a GCP Identity Platform User."""

    uid: UUID
    name: str
    email: str
    phone_number: str
    units_preference: str
    roles: List[Role]


@dataclass
class ClientFarm:
    client_uid: UUID
    farm_uid: UUID


@dataclass
class ClientUser:
    client_uid: UUID
    user_uid: UUID
