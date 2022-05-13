import base64
import json

import pytest

from fastapi import status

from user_management.core.dependencies import RequestUserCheck, User
from user_management.core.exceptions import AuthenticationError


def test_api_gateway_base64_header():
    """Test `RequestUserCheck.get_user` method for an API Gateway security header known to be not
    compliant with Python's Base64 module.
    """
    payload = "eyJuYW1lIjoiTXlyb3NsYXYgVGFudHN5dXJhIiwic3RhZmYiOnRydWUsInJvbGVzIjp7fSwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL2h1bW1pbmdiaXJkdGVjaC1wcm9kdWN0aW9uIiwiYXVkIjoiaHVtbWluZ2JpcmR0ZWNoLXByb2R1Y3Rpb24iLCJhdXRoX3RpbWUiOjE2NTIzNzI1MjEsInVzZXJfaWQiOiIwMjllZjAwNC1hNGJmLTQxM2ItOGU4MS0yYjUxOGM4NzE0Y2UiLCJzdWIiOiIwMjllZjAwNC1hNGJmLTQxM2ItOGU4MS0yYjUxOGM4NzE0Y2UiLCJpYXQiOjE2NTIzNzI1MjEsImV4cCI6MTY1MjM3NjEyMSwiZW1haWwiOiJteXJvc2xhdkBodW1taW5nYmlyZHRlY2guY29tIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbIm15cm9zbGF2QGh1bW1pbmdiaXJkdGVjaC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJwYXNzd29yZCJ9fQ"

    checked_user = RequestUserCheck().get_user(x_apigateway_api_userinfo=payload)
    assert checked_user == User(uid="029ef004-a4bf-413b-8e81-2b518c8714ce", roles={}, staff=True)


def test_no_api_gateway_header():
    """GCP API Gateway header is mandatory to let users in."""
    with pytest.raises(AuthenticationError) as excinfo:
        RequestUserCheck().get_user(x_apigateway_api_userinfo=None)

    assert excinfo.value.context == {"message": "Missing user information in request."}
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_invalid_api_gateway_header_no_user_id():
    """The decoded Base64 header payload must have a `user_id` field to be valid."""
    payload = base64.b64encode(
        json.dumps(
            # This is a mock of a normal GCP API Gateway request, just missing `user_id` field.
            {
                "name": "John Doe",
                "staff": True,
                "roles": {},
                "iss": "https://securetoken.google.com/hummingbirdtech-production",
                "aud": "hummingbirdtech-production",
                "auth_time": 1652372521,
                "sub": "029ef004-a4bf-413b-8e81-2b518c8714ce",
                "iat": 1652372521,
                "exp": 1652376121,
                "email": "john.doe@hummingbirdtech.com",
                "email_verified": False,
                "firebase": {
                    "identities": {"email": ["john.doe@hummingbirdtech.com"]},
                    "sign_in_provider": "password",
                },
            }
        ).encode("utf-8")
    ).decode("utf-8")

    with pytest.raises(AuthenticationError) as excinfo:
        RequestUserCheck().get_user(x_apigateway_api_userinfo=payload)

    assert excinfo.value.context == {"message": "Invalid user information payload."}
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_invalid_api_gateway_header_no_staff():
    """The decoded Base64 header payload must have a `staff` field to be valid."""
    payload = base64.b64encode(
        json.dumps(
            # This is a mock of a normal GCP API Gateway request, just missing `staff` field.
            {
                "name": "John Doe",
                "user_id": "029ef004-a4bf-413b-8e81-2b518c8714ce",
                "roles": {},
                "iss": "https://securetoken.google.com/hummingbirdtech-production",
                "aud": "hummingbirdtech-production",
                "auth_time": 1652372521,
                "sub": "029ef004-a4bf-413b-8e81-2b518c8714ce",
                "iat": 1652372521,
                "exp": 1652376121,
                "email": "john.doe@hummingbirdtech.com",
                "email_verified": False,
                "firebase": {
                    "identities": {"email": ["john.doe@hummingbirdtech.com"]},
                    "sign_in_provider": "password",
                },
            }
        ).encode("utf-8")
    ).decode("utf-8")

    with pytest.raises(AuthenticationError) as excinfo:
        RequestUserCheck().get_user(x_apigateway_api_userinfo=payload)

    assert excinfo.value.context == {"message": "Invalid user information payload."}
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
