import base64
import binascii
import json
from typing import Generator, TypeVar

from fastapi import Header
from sqlalchemy.orm import scoped_session, Session

from user_management.core.database import db_session_factory
from user_management.core.exceptions import AuthenticationError


DBSession = TypeVar("DBSession", scoped_session, Session)


def get_database() -> Generator[scoped_session, None, None]:
    session_factory = db_session_factory()
    db_session = scoped_session(session_factory)

    try:
        yield db_session
    finally:
        db_session.remove()


def get_user_info(x_apigateway_api_userinfo: str = Header(None)) -> dict:
    """Looks up for a GCP Identity Platform header 'X-Apigateway-Api-Userinfo', where the request
    user information is passed, encoded in Base64, after a successful JWT check which is performed
    in GCP side.
    """
    if x_apigateway_api_userinfo is None:
        raise AuthenticationError({"message": "Missing user information in request."})

    try:
        return json.loads(base64.b64decode(x_apigateway_api_userinfo))
    except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise AuthenticationError({"message": "Invalid user information payload."}) from error
