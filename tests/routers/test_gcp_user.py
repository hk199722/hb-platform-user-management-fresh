import json
import uuid
from unittest.mock import patch

import pytest

from fastapi import status
from firebase_admin.auth import (
    EmailAlreadyExistsError,
    PhoneNumberAlreadyExistsError,
    UidAlreadyExistsError,
    UserNotFoundError,
)
from firebase_admin.exceptions import InvalidArgumentError
from sqlalchemy import func, select

from user_management.models import Client, ClientUser, GCPUser, Role
from user_management.schemas import GCPUserSchema


@pytest.mark.parametrize(
    ["user_name", "user_email", "user_phone", "role", "expected_status"],
    [
        pytest.param(
            "",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            None,
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user creation - No user name",
        ),
        pytest.param(
            "John Doe",
            "",
            "+4402081232389",
            None,
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user creation - No user email",
        ),
        pytest.param(
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            status.HTTP_409_CONFLICT,
            id="Wrong user creation - Duplicated user email",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "",
            {"client_uid": str(uuid.uuid4()), "role": Role.NORMAL_USER.value},
            status.HTTP_403_FORBIDDEN,
            id="Wrong user update - role specified with invalid client",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": "INVALID_ROLE"},
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user update - role specified with invalid role",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "+44 02081232389",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            status.HTTP_201_CREATED,
            id="Successful new user creation",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            status.HTTP_201_CREATED,
            id="Successful new user creation - no phone number required",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            status.HTTP_201_CREATED,
            id="Successful new user creation - with role specified",
        ),
    ],
)
@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
def test_create_gcp_user(
    mock_identity_platform,
    test_client,
    user_info,
    test_db_session,
    sql_factory,
    user_name,
    user_email,
    user_phone,
    role,
    expected_status,
):
    mock_identity_platform().sync_gcp_user.side_effect = None  # Mock out GCP-IP access.
    client = sql_factory.client.create(uid="f6787d5d-2577-4663-8de6-88b48c679109")
    sql_factory.gcp_user.create(email="john.doe@hummingbirdtech.com")

    # Add request user to `Client`, so we can assign the role successfully when needed.
    sql_factory.client_user.create(user=user_info.user, client=client, role=Role.SUPERUSER)

    response = test_client.post(
        "/api/v1/users",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={"name": user_name, "email": user_email, "phone_number": user_phone, "role": role},
    )

    assert response.status_code == expected_status, response.json()
    if response.status_code == status.HTTP_201_CREATED:
        gcp_user_uid = response.json()["uid"]
        gcp_user = test_db_session.get(GCPUser, gcp_user_uid)
        assert gcp_user.name == user_name
        assert gcp_user.email == user_email
        # User phones normalization.
        if gcp_user.phone_number is not None:
            assert gcp_user.phone_number == user_phone.replace(" ", "")

        if role is not None:
            # Role passed, and new role created successfully.
            assert response.json()["clients"] == [
                {
                    "client_uid": "f6787d5d-2577-4663-8de6-88b48c679109",
                    "role": Role.NORMAL_USER.value,
                }
            ]

            client_user = test_db_session.scalar(
                select(ClientUser).filter_by(gcp_user_uid=gcp_user_uid, client_uid=client.uid)
            )
            assert client_user is not None


@pytest.mark.parametrize(
    ["user_name", "user_email", "user_phone", "role", "gcp_ip_error", "expected_status"],
    [
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "+44 555 435 7911",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            EmailAlreadyExistsError(
                message="The user with the provided email already exists",
                cause="EMAIL_EXISTS",
                http_response=None,
            ),
            status.HTTP_409_CONFLICT,
            id="Wrong user syncing with GCP - duplicated email",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "+44 555 435 7911",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            UidAlreadyExistsError(
                message="The user with the provided uid already exists",
                cause="DUPLICATE_LOCAL_ID",
                http_response=None,
            ),
            status.HTTP_409_CONFLICT,
            id="Wrong user syncing with GCP - duplicated UID",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "+44 555 435 7911",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            PhoneNumberAlreadyExistsError(
                message="The user with the provided phone number already exists",
                cause="PHONE_NUMBER_EXISTS",
                http_response=None,
            ),
            status.HTTP_409_CONFLICT,
            id="Wrong user syncing with GCP - duplicated phone number",
        ),
        pytest.param(
            "Jane Doe",
            # Need real email to pass our own validation. We are testing responses from GCP-IP only.
            "jane.doe@hummingbirdtech.com",
            "+445554357911",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            ValueError('Malformed email address string: "NOT-AN-EMAIL".'),
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user syncing with GCP - invalid email address",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "+4455",  # GCP-IP thoroughly checks phone numbers on its backend side (but not in SDK).
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            InvalidArgumentError(
                message="Error while calling Auth service",
                cause="INVALID_PHONE_NUMBER. TOO_SHORT",
                http_response=None,
            ),
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user syncing with GCP - invalid phone number",
        ),
    ],
)
@patch("user_management.services.gcp_identity.init_identity_platform_app")
@patch("user_management.services.gcp_identity.create_user")
def test_create_sync_gcp_user_errors(
    mock_identity_platform,
    mock_init_gcp_ip_app,  # Mock initializing GCP-IP/Firebase app. pylint: disable=unused-argument
    test_client,
    user_info,
    test_db_session,
    sql_factory,
    user_name,
    user_email,
    user_phone,
    role,
    gcp_ip_error,
    expected_status,
):
    mock_identity_platform.side_effect = gcp_ip_error

    client = sql_factory.client.create(uid="f6787d5d-2577-4663-8de6-88b48c679109")
    sql_factory.client_user.create(client=client, user=user_info.user, role=Role.SUPERUSER)

    response = test_client.post(
        "/api/v1/users",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={"name": user_name, "email": user_email, "phone_number": user_phone, "role": role},
    )

    assert response.status_code == expected_status, response.json()

    gcp_user_uid = response.json().get("context", {}).get("uid")
    assert gcp_user_uid is not None

    # User has been created anyway in local DB.
    gcp_user = test_db_session.get(GCPUser, gcp_user_uid)
    assert gcp_user.name == user_name
    assert gcp_user.email == user_email
    # User phones normalization.
    assert gcp_user.phone_number == user_phone.replace(" ", "")

    # Role passed, and new role created successfully.
    client_user = test_db_session.scalar(
        select(ClientUser).filter_by(gcp_user_uid=gcp_user_uid, client_uid=client.uid)
    )
    assert client_user is not None


@pytest.mark.parametrize(
    ["user_uid", "expected_status"],
    [
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            status.HTTP_200_OK,
            id="Successful user detail retrieval",
        ),
        pytest.param(
            "47294de0-8999-49c1-add4-6f8ac833ea6d",
            status.HTTP_404_NOT_FOUND,
            id="Wrong user retrieval - Non existent user UID",
        ),
    ],
)
def test_get_gcp_user(test_client, user_info, sql_factory, user_uid, expected_status):
    gcp_user = sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")
    client_user = sql_factory.client_user.create(client=user_info.client_1, user=gcp_user)

    response = test_client.get(
        f"/api/v1/users/{user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_200_OK:
        expected = {
            "uid": str(gcp_user.uid),
            "name": gcp_user.name,
            "email": gcp_user.email,
            # User phones normalization.
            "phone_number": gcp_user.phone_number.replace(" ", ""),
            "staff": gcp_user.staff,
            "clients": [
                {"client_uid": str(client_user.client.uid), "role": client_user.role.value}
            ],
        }
        assert response.json() == expected


def test_list_gcp_users(test_client, user_info, sql_factory):
    # 3 GCPUsers under the same Client as the request user. Those will be shown in response.
    client_users = sql_factory.client_user.create_batch(size=3, client=user_info.client_1)
    # 3 more GCPUsers in another client the request user does NOT belong to. Those will be hidden.
    sql_factory.client_user.create_batch(size=3)

    response = test_client.get(
        "/api/v1/users", headers={"X-Apigateway-Api-Userinfo": user_info.header_payload}
    )

    assert response.status_code == status.HTTP_200_OK

    # The 3 test users...
    expected_users = [
        {
            "uid": str(client_user.user.uid),
            "name": client_user.user.name,
            "email": client_user.user.email,
            # User phones normalization.
            "phone_number": client_user.user.phone_number.replace(" ", ""),
            "staff": client_user.user.staff,
            "clients": [
                {"client_uid": str(client_user.client.uid), "role": client_user.role.value}
            ],
        }
        for client_user in client_users
    ]
    # ...and the request user.
    expected_users.append(
        {
            "uid": str(user_info.user.uid),
            "name": user_info.user.name,
            "email": user_info.user.email,
            # User phones normalization.
            "phone_number": user_info.user.phone_number.replace(" ", ""),
            "staff": user_info.user.staff,
            "clients": [
                {"client_uid": str(client_user.client.uid), "role": client_user.role.value}
                for client_user in user_info.user.clients
            ],
        }
    )
    data = response.json()

    assert len(data) == 4
    for user in expected_users:
        assert user in data


@pytest.mark.parametrize(
    ["user_uid", "patch_payload", "expected_status"],
    [
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            {"email": "john.doe@hummingbirdtech.com"},
            status.HTTP_200_OK,
            id="Successful user update - email updated",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            {"name": "John Doe"},
            status.HTTP_200_OK,
            id="Successful user update - name updated",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            {"phone_number": "+4402081232389"},
            status.HTTP_200_OK,
            id="Successful user update - phone number updated",
        ),
    ],
)
@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
def test_update_gcp_user_success(
    mock_identity_platform,
    test_client,
    user_info,
    test_db_session,
    sql_factory,
    user_uid,
    patch_payload,
    expected_status,
):
    mock_identity_platform().sync_gcp_user.side_effect = None  # Mock out GCP-IP access.
    gcp_user = sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")
    # Relate the user to be updated with a `Client` in which the request user does have permissions.
    sql_factory.client_user.create(client=user_info.client_1, user=gcp_user)

    response = test_client.patch(
        f"/api/v1/users/{user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json=patch_payload,
    )
    data = response.json()

    assert response.status_code == expected_status, data

    test_db_session.expire_all()
    modified_user = test_db_session.get(GCPUser, user_uid)

    for key, value in patch_payload.items():
        # Check response payload.
        assert data[key] == value

        # Check that user data was effectively updated in DB.
        assert getattr(modified_user, key) == value


@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
def test_update_gcp_user_role_success(
    mock_identity_platform, test_client, user_info, test_db_session, sql_factory
):
    mock_identity_platform().sync_gcp_user.side_effect = None  # Mock out GCP-IP access.
    # GCPUser, already belongs to Client 2.
    gcp_user = sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")
    sql_factory.client_user.create(client=user_info.client_2, user=gcp_user, role=Role.PILOT)

    # Update the user to be a member of `client_1` of the request user.
    response = test_client.patch(
        f"/api/v1/users/{gcp_user.uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={"role": {"client_uid": str(user_info.client_1.uid), "role": Role.NORMAL_USER.value}},
    )
    data = response.json()

    assert response.status_code == status.HTTP_200_OK, data
    assert data == {
        "name": gcp_user.name,
        "phone_number": gcp_user.phone_number,
        "email": gcp_user.email,
        "staff": gcp_user.staff,
        "uid": gcp_user.uid,
        "clients": [{"client_uid": str(user_info.client_1.uid), "role": Role.NORMAL_USER.value}],
    }

    # Check that user data was effectively updated in DB. We have now 2 roles for our user: one with
    # the Client 1, which was already present, and another we just added, for Client 2.
    test_db_session.expire_all()
    modified_user = test_db_session.get(GCPUser, gcp_user.uid)
    client_user = test_db_session.scalar(
        select(ClientUser).filter_by(gcp_user_uid=gcp_user.uid, client_uid=user_info.client_1.uid)
    )
    assert client_user in modified_user.clients


@pytest.mark.parametrize(
    ["user_uid", "user_name", "user_email", "user_phone", "role", "expected_status"],
    [
        pytest.param(
            "a0723fb5-6b0f-45ec-a131-6a6a1bd87741",
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            None,
            status.HTTP_404_NOT_FOUND,
            id="Wrong user update - Non existent user UID",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "John Doe",
            "",
            "+4402081232389",
            None,
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user update - No user email",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            None,
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user update - No user name",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "+4402081232389",
            None,
            status.HTTP_409_CONFLICT,
            id="Wrong user update - Duplicating existent user email",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            status.HTTP_409_CONFLICT,
            id="Wrong user update - role already registered",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            {"client_uid": str(uuid.uuid4()), "role": Role.NORMAL_USER.value},
            status.HTTP_404_NOT_FOUND,
            id="Wrong user update - role specified with invalid client",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            {"client_uid": str(uuid.uuid4()), "role": "INVALID_ROLE"},
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user update - role specified with invalid role",
        ),
    ],
)
@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
def test_update_gcp_user_errors(
    mock_identity_platform,
    test_client,
    user_info,
    test_db_session,
    sql_factory,
    user_uid,
    user_name,
    user_email,
    user_phone,
    role,
    expected_status,
):
    mock_identity_platform().sync_gcp_user.side_effect = None  # Mock out GCP-IP access.
    gcp_user = sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")
    # Create Client to join `gcp_user` and request user under a same client. So request user can
    # actually have permission to perform requests within that client.
    client_1 = sql_factory.client.create(uid="f6787d5d-2577-4663-8de6-88b48c679109")
    sql_factory.client_user.create(client=client_1, user=user_info.user)
    sql_factory.client_user.create(client=client_1, user=gcp_user, role=Role.NORMAL_USER)
    sql_factory.client_user.create(client=user_info.client_1, user=gcp_user)
    # Create a user for the duplicate email error.
    sql_factory.gcp_user.create(email="jane.doe@hummingbirdtech.com")

    response = test_client.patch(
        f"/api/v1/users/{user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={"name": user_name, "email": user_email, "phone_number": user_phone, "role": role},
    )

    assert response.status_code == expected_status, response.json()

    # Check that user data was NOT updated in DB.
    test_db_session.expire_all()
    modified_user = test_db_session.get(GCPUser, user_uid)
    if modified_user:
        assert modified_user.name == gcp_user.name
        assert modified_user.email == gcp_user.email
        assert modified_user.phone_number == gcp_user.phone_number


@pytest.mark.parametrize(
    [
        "user_uid",
        "user_name",
        "user_email",
        "user_phone",
        "role",
        "gcp_ip_error",
        "expected_status",
    ],
    [
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            UserNotFoundError(
                message="No user record found for the given identifier",
                cause="USER_NOT_FOUND",
                http_response=None,
            ),
            status.HTTP_404_NOT_FOUND,
            id="Wrong user syncing with GCP - Non existent user UID",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            PhoneNumberAlreadyExistsError(
                message="The user with the provided phone number already exists",
                cause="PHONE_NUMBER_EXISTS",
                http_response=None,
            ),
            status.HTTP_409_CONFLICT,
            id="Wrong user syncing with GCP - duplicated phone number",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "John Doe",
            # Need real email to pass our own validation. We are testing responses from GCP-IP only.
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            ValueError('Malformed email address string: "NOT-AN-EMAIL".'),
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user syncing with GCP - invalid email address",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+440",  # GCP-IP thoroughly checks phone numbers on its backend side (but not in SDK).
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            InvalidArgumentError(
                message="Error while calling Auth service",
                cause="INVALID_PHONE_NUMBER. TOO_SHORT",
                http_response=None,
            ),
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user syncing with GCP - invalid phone number",
        ),
    ],
)
@patch("user_management.services.gcp_identity.init_identity_platform_app")
@patch("user_management.services.gcp_identity.update_user")
def test_update_sync_gcp_user_errors(
    mock_identity_platform,
    mock_init_gcp_ip_app,  # Mock initializing GCP-IP/Firebase app. pylint: disable=unused-argument
    test_client,
    user_info,
    test_db_session,
    sql_factory,
    user_uid,
    user_name,
    user_email,
    user_phone,
    role,
    gcp_ip_error,
    expected_status,
):
    mock_identity_platform.side_effect = gcp_ip_error

    # Create the `Client` and the `GCPUser` we want to join it.
    client = sql_factory.client.create(uid="f6787d5d-2577-4663-8de6-88b48c679109")
    user = sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")
    sql_factory.client_user.create(client=user_info.client_1, user=user)
    # Make the request user also a member of the `Client`, so he can actually modify the user.
    sql_factory.client_user.create(client=client, user=user_info.user, role=Role.SUPERUSER)

    response = test_client.patch(
        f"/api/v1/users/{user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={"name": user_name, "email": user_email, "phone_number": user_phone, "role": role},
    )

    assert response.status_code == expected_status, response.json()

    gcp_user_uid = response.json().get("context", {}).get("uid")
    assert gcp_user_uid is not None

    # User has been updated anyway in local DB.
    test_db_session.expire_all()
    gcp_user = test_db_session.get(GCPUser, gcp_user_uid)
    assert gcp_user.name == user_name
    assert gcp_user.email == user_email
    # User phones normalization.
    assert gcp_user.phone_number == user_phone.replace(" ", "")

    # Role passed, and new role created successfully.
    client_user = test_db_session.scalar(
        select(ClientUser).filter_by(gcp_user_uid=gcp_user_uid, client_uid=client.uid)
    )
    assert client_user is not None


@pytest.mark.parametrize(
    ["user_uid", "expected_status"],
    [
        pytest.param(
            "a0723fb5-6b0f-45ec-a131-6a6a1bd87741",
            status.HTTP_404_NOT_FOUND,
            id="Wrong user deletion - Non existent user UID",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            status.HTTP_204_NO_CONTENT,
            id="Successful user deletion",
        ),
    ],
)
@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
def test_delete_gcp_user(
    mock_identity_platform,
    test_client,
    user_info,
    test_db_session,
    sql_factory,
    user_uid,
    expected_status,
):
    mock_identity_platform().remove_gcp_user.side_effect = None  # Mock out GCP-IP access.
    gcp_user = sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")
    client_user = sql_factory.client_user.create(user=gcp_user, client=user_info.client_1)
    test_db_session.commit()

    response = test_client.delete(
        f"/api/v1/users/{user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_204_NO_CONTENT:
        assert (
            test_db_session.scalar(
                select(func.count()).select_from(GCPUser).filter_by(uid=gcp_user.uid)
            )
            == 0
        )
        # Check that user Client is still there.
        assert (
            test_db_session.scalar(
                select(func.count()).select_from(Client).filter_by(uid=client_user.client_uid)
            )
            == 1
        )

        # Check that the related ClientUser is also removed.
        assert (
            test_db_session.scalar(
                select(func.count())
                .select_from(ClientUser)
                .filter_by(client=client_user.client, user=client_user.user)
            )
            == 0
        )


@pytest.mark.parametrize(
    ["user_uid", "gcp_ip_error", "expected_status"],
    [
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            UserNotFoundError(
                message="No user record found for the given identifier",
                cause="USER_NOT_FOUND",
                http_response=None,
            ),
            status.HTTP_404_NOT_FOUND,
            id="Wrong user deletion syncing with GCP - Non existent user UID",
        ),
    ],
)
@patch("user_management.services.gcp_identity.delete_user")
def test_delete_sync_gcp_user_errors(
    mock_identity_platform,
    test_client,
    user_info,
    test_db_session,
    sql_factory,
    user_uid,
    gcp_ip_error,
    expected_status,
):
    mock_identity_platform.side_effect = gcp_ip_error
    gcp_user = sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")
    user_client = sql_factory.client_user.create(user=gcp_user, client=user_info.client_1)
    test_db_session.commit()

    response = test_client.delete(
        f"/api/v1/users/{user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == expected_status
    # Check that User and its Client is still there. Users must be first deleted from GCP-IP backend
    # and later from local DB. If any problem occurs in GCP-IP the user must remain in DB as well.
    assert (
        test_db_session.scalar(
            select(func.count()).select_from(GCPUser).filter_by(uid=gcp_user.uid)
        )
        == 1
    )
    assert (
        test_db_session.scalar(
            select(func.count()).select_from(Client).filter_by(uid=user_client.client_uid)
        )
        == 1
    )


def test_delete_client_user(test_client, user_info, test_db_session, sql_factory):
    client_user = sql_factory.client_user.create(client=user_info.client_1)

    response = test_client.delete(
        f"/api/v1/users/{client_user.gcp_user_uid}/roles/{user_info.client_1.uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()

    # Check that the object has been effectively deleted from the database.
    assert (
        test_db_session.scalar(
            select(func.count())
            .select_from(ClientUser)
            .filter_by(client=client_user.client, user=client_user.user)
        )
        == 0
    )


@pytest.mark.parametrize(
    ["user_uid", "expected_status"],
    [
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            status.HTTP_204_NO_CONTENT,
            id="Successful password reset link request",
        ),
        pytest.param(
            "a0723fb5-6b0f-45ec-a131-6a6a1bd87741",
            status.HTTP_404_NOT_FOUND,
            id="Wrong password reset link request - Non existent user UID",
        ),
    ],
)
@patch("user_management.services.mailer.GCPIdentityPlatformService")
@patch("user_management.services.mailer.PublisherClient")
def test_reset_gcp_user_password(
    mock_pubsub, mock_identity_platform, test_client, sql_factory, user_uid, expected_status
):
    mock_identity_platform = mock_identity_platform()
    mock_pubsub = mock_pubsub()
    link = "http://hummingbirdtech.com/reset-link"
    mock_identity_platform.get_password_reset_link.return_value = link
    gcp_user = sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")

    response = test_client.get(f"/api/v1/users/{user_uid}/reset-password")

    assert response.status_code == expected_status

    if expected_status == status.HTTP_204_NO_CONTENT:
        message = {
            "message_type": "PASSWORD_RESET",
            "email": gcp_user.email,
            "context": {"full_name": gcp_user.name, "reset_password_link": link},
        }
        mock_pubsub.publish.assert_called_with(
            mock_pubsub.topic_path(), json.dumps(message).encode("utf-8")
        )
        mock_identity_platform.get_password_reset_link.assert_called_with(
            GCPUserSchema(
                uid=gcp_user.uid,
                name=gcp_user.name,
                phone_number=gcp_user.phone_number,
                email=gcp_user.email,
                clients=[],
            )
        )
