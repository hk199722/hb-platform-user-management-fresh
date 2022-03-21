import json
from unittest.mock import patch

import pytest
from fastapi import status
from requests.models import Response

from tests.auth.mocks import successful_login, wrong_api_key, wrong_email, wrong_password


@pytest.mark.parametrize(
    [
        "login_payload",
        "gcp_response_code",
        "gcp_response_content",
        "expected_status",
        "expected_response",
    ],
    [
        pytest.param(
            {"email": "john.doe@hummingbirdtech.com", "password": "secret"},
            status.HTTP_200_OK,
            successful_login(),
            status.HTTP_200_OK,
            json.loads(successful_login()),
            id="Successful login",
        ),
        pytest.param(
            {"email": "WRONG@hummingbirdtech.com", "password": "secret"},
            status.HTTP_400_BAD_REQUEST,
            wrong_email(),
            status.HTTP_401_UNAUTHORIZED,
            {
                "app_exception": "AuthenticationError",
                "context": {"message": "Invalid credentials."},
            },
            id="Wrong login - invalid email",
        ),
        pytest.param(
            {"email": "john.doe@hummingbirdtech.com", "password": "WRONG"},
            status.HTTP_400_BAD_REQUEST,
            wrong_password(),
            status.HTTP_401_UNAUTHORIZED,
            {
                "app_exception": "AuthenticationError",
                "context": {"message": "Invalid credentials."},
            },
            id="Wrong login - invalid password",
        ),
        pytest.param(
            {"email": "john.doe@hummingbirdtech.com", "password": "secret"},
            status.HTTP_400_BAD_REQUEST,
            wrong_api_key(),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {"app_exception": "RemoteServiceError", "context": {"message": "Service unavailable."}},
            id="Wrong login - Service configuration error",
        ),
    ],
)
@patch("user_management.services.gcp_identity.Session")
def test_login(
    mock_response,
    test_client,
    login_payload,
    gcp_response_code,
    gcp_response_content,
    expected_status,
    expected_response,
):
    gcp_response = Response()
    gcp_response.status_code = gcp_response_code
    gcp_response._content = gcp_response_content
    mock_response().post.return_value = gcp_response

    response = test_client.post("/api/v1/login", json=login_payload)

    assert response.status_code == expected_status
    assert response.json() == expected_response
