import re
from typing import List, Optional

from pydantic import BaseModel, EmailStr, UUID4, validator

from user_management.models import Role


PHONE_PATTERN = re.compile(r"\+[0-9 ]+")


class NamedModel(BaseModel):
    name: str

    @validator("name", pre=True, always=True)
    def empty_string(cls, value):  # pylint: disable=no-self-argument
        return value if value != "" else None


class ClientSchema(NamedModel):
    uid: UUID4

    class Config:
        orm_mode = True


class NewClientSchema(NamedModel):
    pass


class ClientUserSchema(BaseModel):
    client_uid: UUID4
    role: Role

    class Config:
        orm_mode = True


class BaseUserModel(NamedModel):
    phone_number: str = ""
    email: EmailStr
    staff: bool = False

    @validator("phone_number")
    def valid_phone_number(cls, value):  # pylint: disable=no-self-argument
        if value and PHONE_PATTERN.match(value) is None:
            raise ValueError(
                f"{value} is not a valid phone number. Accepted phone numbers are E.164 compliant "
                f"(+<area code><phone number>)."
            )

        return value.replace(" ", "")


class GCPUserSchema(BaseUserModel):
    uid: UUID4
    clients: List[ClientUserSchema]

    class Config:
        orm_mode = True


class NewGCPUserSchema(BaseUserModel):
    role: Optional[ClientUserSchema] = None


class ClientFarmSchema(BaseModel):
    farm_uid: UUID4
    client_uid: UUID4

    class Config:
        orm_mode = True
