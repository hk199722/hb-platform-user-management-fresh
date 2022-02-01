import re
from typing import List, Optional

from pydantic import BaseModel, EmailStr, SecretStr, UUID4, validator

from user_management.models import Role


PHONE_PATTERN = re.compile(r"\+[0-9 ]+")


def check_empty_string(value: str) -> str:
    """Checks that the submitted values are not empty strings."""
    if value == "":
        raise ValueError("Empty names are not allowed.")

    return value


def check_phone_number(value: Optional[str]) -> Optional[str]:
    """Normalizes the submitted phone numbers by trimming spaces in the string."""
    if value:
        if PHONE_PATTERN.match(value) is None:
            raise ValueError(
                f"{value} is not a valid phone number. Accepted phone numbers are E.164 "
                f"compliant (+<area code><phone number>)."
            )

        return value.replace(" ", "")

    return None


class ClientSchema(BaseModel):
    name: str
    uid: UUID4

    _validate_name = validator("name", pre=True, always=True, allow_reuse=True)(check_empty_string)

    class Config:
        orm_mode = True


class NewClientSchema(BaseModel):
    name: str

    _validate_name = validator("name", pre=True, always=True, allow_reuse=True)(check_empty_string)


class ClientUserSchema(BaseModel):
    client_uid: UUID4
    role: Role

    class Config:
        orm_mode = True


class GCPUserSchema(BaseModel):
    uid: UUID4
    name: str
    phone_number: Optional[str] = ""
    email: EmailStr
    staff: bool = False
    clients: List[ClientUserSchema]

    _validate_name = validator("name", pre=True, always=True, allow_reuse=True)(check_empty_string)
    _validate_phone = validator("phone_number", pre=True, always=True, allow_reuse=True)(
        check_phone_number
    )

    class Config:
        orm_mode = True


class NewGCPUserSchema(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[str] = ""
    staff: bool = False
    role: Optional[ClientUserSchema] = None

    _validate_name = validator("name", pre=True, always=True, allow_reuse=True)(check_empty_string)
    _validate_phone = validator("phone_number", pre=True, always=True, allow_reuse=True)(
        check_phone_number
    )


class UpdateGCPUserSchema(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    staff: Optional[bool]
    role: Optional[ClientUserSchema] = None

    _validate_name = validator("name", pre=True, always=True, allow_reuse=True)(check_empty_string)
    _validate_phone = validator("phone_number", pre=True, always=True, allow_reuse=True)(
        check_phone_number
    )


class ClientFarmSchema(BaseModel):
    farm_uid: UUID4
    client_uid: UUID4

    class Config:
        orm_mode = True


class CreateSecurityTokenSchema(BaseModel):
    gcp_user_uid: UUID4


class SecurityTokenSchema(BaseModel):
    uid: UUID4
    gcp_user_uid: UUID4

    class Config:
        orm_mode = True


class CreatePasswordSchema(BaseModel):
    password: SecretStr
    verified_password: SecretStr

    @validator("verified_password")
    def passwords_match(cls, value, values):  # pylint: disable=no-self-argument
        if "password" in values and value != values["password"]:
            raise ValueError("Passwords do not match.")

        return value
