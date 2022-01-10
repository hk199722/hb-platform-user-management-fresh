import base64
import binascii
import dataclasses
import json
from typing import Dict, Generator, TypeVar

from fastapi import Header
from pydantic import UUID4
from sqlalchemy.orm import scoped_session, Session

from user_management.core.database import db_session_factory
from user_management.core.exceptions import AuthenticationError


DBSession = TypeVar("DBSession", scoped_session, Session)


@dataclasses.dataclass
class User:
    """User definition object to be passed to logic from the GCP Identity Platform user info
    payload. It represents the authenticated user who makes the request to the API.
    """

    uid: UUID4
    staff: bool
    roles: Dict[str, str]


def get_database() -> Generator[scoped_session, None, None]:
    session_factory = db_session_factory()
    db_session = scoped_session(session_factory)

    try:
        yield db_session
    finally:
        db_session.remove()


def get_user(x_apigateway_api_userinfo: str = Header(None)) -> User:
    """Looks up for a GCP Identity Platform header 'X-Apigateway-Api-Userinfo', where the request
    user information is passed, encoded in Base64, after a successful JWT check which is performed
    in GCP side.
    """
    if x_apigateway_api_userinfo is None:
        raise AuthenticationError({"message": "Missing user information in request."})

    try:
        user_info = json.loads(base64.b64decode(x_apigateway_api_userinfo))
        return User(
            uid=user_info["uid"],
            staff=user_info["staff"],
            roles=user_info.get("roles", {}),
        )
    except (binascii.Error, json.JSONDecodeError, KeyError, UnicodeDecodeError) as error:
        raise AuthenticationError({"message": "Invalid user information payload."}) from error
