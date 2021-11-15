from pydantic import BaseModel, EmailStr, UUID4


class Client(BaseModel):
    uid: UUID4
    name: str


class NewClient(BaseModel):
    name: str


class GCPUser(BaseModel):
    uid: UUID4
    name: str
    email: EmailStr
    phone_number: str
    # TODO: roles


class ClientFarm(BaseModel):
    farm_uid: UUID4
    client_uid: UUID4
