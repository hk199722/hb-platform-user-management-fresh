# pylint: disable=protected-access
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status

from tests.auth.mocks import (
    expired_refresh_token,
    invalid_refresh_token,
    refresh_token_user_deleted,
    refresh_token_user_disabled,
    successful_login,
    successful_refresh_token,
    wrong_api_key,
    wrong_email,
    wrong_password,
)


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
            successful_login(),
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
@patch("user_management.services.gcp_identity.ClientSession.post")
def test_login(
    mock_aiohttp,
    test_client,
    login_payload,
    gcp_response_code,
    gcp_response_content,
    expected_status,
    expected_response,
):
    # gcp_response = Response()
    # gcp_response.status_code = gcp_response_code
    # gcp_response._content = gcp_response_content
    # mock_response().post.return_value = gcp_response
    mock_gcp_response = AsyncMock()
    mock_gcp_response.status = gcp_response_code
    mock_gcp_response.json.return_value = gcp_response_content
    mock_aiohttp.return_value.__aenter__.return_value = mock_gcp_response

    response = test_client.post("/api/v1/login", json=login_payload)

    assert response.status_code == expected_status
    assert response.json() == expected_response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    [
        "refresh_token",
        "gcp_response_content",
        "gcp_response_code",
        "expected_status",
        "expected_response",
    ],
    [
        pytest.param(
            "AIwUaOmXReh98IRp91r5v2aJyOPMzgu4OC-v4EJSUX7v7sEC3qWznqsgTC68Ldy_6OPdR_x12H3cioy7OaW2nEycR1N45N63HLZLueUivPh3Hcpy1kZP0-Nr6ww8vaOX06JitcMc_sp6ObsiEf_Wfn0cWvNA4n-uwjdbMtr4FmI0scYxgDhN2n05gKbViJNLpikguxeVDsVei8Erdz-78iYjiHVDOTtnyC2cqpma4VSylGLpOvqIjzQnIUcxOaq7gHu6KrNVvlVN",
            successful_refresh_token(),
            status.HTTP_200_OK,
            status.HTTP_200_OK,
            successful_refresh_token(),
            id="Successful refresh token request",
        ),
        pytest.param(
            "NOT-REALLY-A-TOKEN",
            invalid_refresh_token(),
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            {
                "app_exception": "AuthenticationError",
                "context": {"message": "Invalid refresh token."},
            },
            id="Wrong refresh token request - Invalid token",
        ),
        pytest.param(
            "AIwUaOmXReh98IRp91r5v2aJyOPMzgu4OC-v4EJSUX7v7sEC3qWznqsgTC68Ldy_6OPdR_x12H3cioy7OaW2nEycR1N45N63HLZLueUivPh3Hcpy1kZP0-Nr6ww8vaOX06JitcMc_sp6ObsiEf_Wfn0cWvNA4n-uwjdbMtr4FmI0scYxgDhN2n05gKbViJNLpikguxeVDsVei8Erdz-78iYjiHVDOTtnyC2cqpma4VSylGLpOvqIjzQnIUcxOaq7gHu6KrNVvlVN",
            expired_refresh_token(),
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            {
                "app_exception": "AuthenticationError",
                "context": {"message": "Token expired. Please log in again."},
            },
            id="Wrong refresh token request - Token expired",
        ),
        pytest.param(
            "AIwUaOmXReh98IRp91r5v2aJyOPMzgu4OC-v4EJSUX7v7sEC3qWznqsgTC68Ldy_6OPdR_x12H3cioy7OaW2nEycR1N45N63HLZLueUivPh3Hcpy1kZP0-Nr6ww8vaOX06JitcMc_sp6ObsiEf_Wfn0cWvNA4n-uwjdbMtr4FmI0scYxgDhN2n05gKbViJNLpikguxeVDsVei8Erdz-78iYjiHVDOTtnyC2cqpma4VSylGLpOvqIjzQnIUcxOaq7gHu6KrNVvlVN",
            refresh_token_user_disabled(),
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            {
                "app_exception": "AuthenticationError",
                "context": {"message": "User has been disabled."},
            },
            id="Wrong refresh token request - User disabled",
        ),
        pytest.param(
            "AIwUaOmXReh98IRp91r5v2aJyOPMzgu4OC-v4EJSUX7v7sEC3qWznqsgTC68Ldy_6OPdR_x12H3cioy7OaW2nEycR1N45N63HLZLueUivPh3Hcpy1kZP0-Nr6ww8vaOX06JitcMc_sp6ObsiEf_Wfn0cWvNA4n-uwjdbMtr4FmI0scYxgDhN2n05gKbViJNLpikguxeVDsVei8Erdz-78iYjiHVDOTtnyC2cqpma4VSylGLpOvqIjzQnIUcxOaq7gHu6KrNVvlVN",
            refresh_token_user_deleted(),
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            {
                "app_exception": "AuthenticationError",
                "context": {"message": "User has been deleted."},
            },
            id="Wrong refresh token request - User deleted",
        ),
        pytest.param(
            "AIwUaOmXReh98IRp91r5v2aJyOPMzgu4OC-v4EJSUX7v7sEC3qWznqsgTC68Ldy_6OPdR_x12H3cioy7OaW2nEycR1N45N63HLZLueUivPh3Hcpy1kZP0-Nr6ww8vaOX06JitcMc_sp6ObsiEf_Wfn0cWvNA4n-uwjdbMtr4FmI0scYxgDhN2n05gKbViJNLpikguxeVDsVei8Erdz-78iYjiHVDOTtnyC2cqpma4VSylGLpOvqIjzQnIUcxOaq7gHu6KrNVvlVN",
            {
                "error": {
                    "code": 400,
                    "message": "WHATEVER GOOGLE SAYS",
                    "status": "INVALID_ARGUMENT",
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {
                "app_exception": "RemoteServiceError",
                "context": {"message": "Unable to refresh token."},
            },
            id="Wrong refresh token request - Random error in GCP",
        ),
    ],
)
@patch("user_management.services.gcp_identity.ClientSession.post")
def test_refresh_token(
    mock_aiohttp,
    test_client,
    refresh_token,
    gcp_response_content,
    gcp_response_code,
    expected_status,
    expected_response,
):
    mock_gcp_response = AsyncMock()
    mock_gcp_response.status = gcp_response_code
    mock_gcp_response.json.return_value = gcp_response_content
    mock_aiohttp.return_value.__aenter__.return_value = mock_gcp_response

    response = test_client.post(
        "/api/v1/login/refresh-token", json={"refresh_token": refresh_token}
    )

    assert response.status_code == expected_status
    assert response.json() == expected_response
