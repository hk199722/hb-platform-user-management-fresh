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
            None,
            status.HTTP_409_CONFLICT,
            id="Wrong user creation - Duplicated user email",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "",
            {"client_uid": str(uuid.uuid4()), "role": Role.NORMAL_USER.value},
            status.HTTP_404_NOT_FOUND,
            id="Wrong user update - role specified with invalid client",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "",
            {"client_uid": str(uuid.uuid4()), "role": "INVALID_ROLE"},
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user update - role specified with invalid role",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "+44 02081232389",
            None,
            status.HTTP_201_CREATED,
            id="Successful new user creation",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "",
            None,
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
@patch("user_management.services.gcp_user.GCPIdentityProviderService")
def test_create_gcp_user(
    mock_identity_provider,
    test_client,
    test_db_session,
    sql_factory,
    user_name,
    user_email,
    user_phone,
    role,
    expected_status,
):
    mock_identity_provider().sync_gcp_user.side_effect = None  # Mock out GCP-IP access.
    client = sql_factory.client.create(uid="f6787d5d-2577-4663-8de6-88b48c679109")
    sql_factory.gcp_user.create(email="john.doe@hummingbirdtech.com")

    response = test_client.post(
        "/api/v1/users",
        json={"name": user_name, "email": user_email, "phone_number": user_phone, "role": role},
    )

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_201_CREATED:
        gcp_user_uid = response.json()["uid"]
        gcp_user = test_db_session.get(GCPUser, gcp_user_uid)
        assert gcp_user.name == user_name
        assert gcp_user.email == user_email
        # User phones normalization.
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
@patch("user_management.services.gcp_identity.create_user")
def test_create_sync_gcp_user_errors(
    mock_identity_provider,
    test_client,
    test_db_session,
    sql_factory,
    user_name,
    user_email,
    user_phone,
    role,
    gcp_ip_error,
    expected_status,
):
    mock_identity_provider.side_effect = gcp_ip_error

    client = sql_factory.client.create(uid="f6787d5d-2577-4663-8de6-88b48c679109")

    response = test_client.post(
        "/api/v1/users",
        json={"name": user_name, "email": user_email, "phone_number": user_phone, "role": role},
    )

    assert response.status_code == expected_status

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
def test_get_gcp_user(test_client, sql_factory, user_uid, expected_status):
    client = sql_factory.client.create()
    gcp_user = sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")
    client_user = sql_factory.client_user.create(client=client, user=gcp_user)

    response = test_client.get(f"/api/v1/users/{user_uid}")

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_200_OK:
        expected = {
            "uid": str(gcp_user.uid),
            "name": gcp_user.name,
            "email": gcp_user.email,
            # User phones normalization.
            "phone_number": gcp_user.phone_number.replace(" ", ""),
            "clients": [
                {"client_uid": str(client_user.client.uid), "role": client_user.role.value}
            ],
        }
        assert response.json() == expected


def test_list_gcp_users(test_client, sql_factory):
    client = sql_factory.client.create()
    client_users = sql_factory.client_user.create_batch(size=3, client=client)

    response = test_client.get("/api/v1/users")

    assert response.status_code == status.HTTP_200_OK
    expected = [
        {
            "uid": str(client_user.user.uid),
            "name": client_user.user.name,
            "email": client_user.user.email,
            # User phones normalization.
            "phone_number": client_user.user.phone_number.replace(" ", ""),
            "clients": [
                {"client_uid": str(client_user.client.uid), "role": client_user.role.value}
            ],
        }
        for client_user in client_users
    ]
    assert response.json() == expected


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
            None,
            status.HTTP_200_OK,
            id="Successful user update",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            {"client_uid": "0a208dde-f68f-4682-b75f-eab67de6a64b", "role": Role.NORMAL_USER.value},
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
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            {"client_uid": "f6787d5d-2577-4663-8de6-88b48c679109", "role": Role.NORMAL_USER.value},
            status.HTTP_200_OK,
            id="Successful user update - with role specified",
        ),
    ],
)
@patch("user_management.services.gcp_user.GCPIdentityProviderService")
def test_update_gcp_user(
    mock_identity_provider,
    test_client,
    test_db_session,
    sql_factory,
    user_uid,
    user_name,
    user_email,
    user_phone,
    role,
    expected_status,
):
    mock_identity_provider().sync_gcp_user.side_effect = None  # Mock out GCP-IP access.
    # Client 1, the Client we will update our GCPUser with when we pass a role to it.
    client_1 = sql_factory.client.create(uid="f6787d5d-2577-4663-8de6-88b48c679109")
    client_2 = sql_factory.client.create(uid="0a208dde-f68f-4682-b75f-eab67de6a64b")
    # GCPUser, already belongs to Client 2.
    gcp_user = sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")
    sql_factory.client_user.create(client=client_2, user=gcp_user)
    sql_factory.gcp_user.create(email="jane.doe@hummingbirdtech.com")

    response = test_client.patch(
        f"/api/v1/users/{user_uid}",
        json={"name": user_name, "email": user_email, "phone_number": user_phone, "role": role},
    )

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_200_OK:
        test_db_session.expire_all()
        modified_user = test_db_session.get(GCPUser, user_uid)
        assert modified_user.name == user_name
        assert modified_user.email == user_email
        assert modified_user.phone_number == user_phone

        if role is not None:
            assert response.json()["clients"] == [
                {
                    "client_uid": "f6787d5d-2577-4663-8de6-88b48c679109",
                    "role": Role.NORMAL_USER.value,
                }
            ]

            client_user = test_db_session.scalar(
                select(ClientUser).filter_by(gcp_user_uid=gcp_user.uid, client_uid=client_1.uid)
            )
            assert client_user is not None


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
@patch("user_management.services.gcp_identity.update_user")
def test_update_sync_gcp_user_errors(
    mock_identity_provider,
    test_client,
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
    mock_identity_provider.side_effect = gcp_ip_error

    client = sql_factory.client.create(uid="f6787d5d-2577-4663-8de6-88b48c679109")
    sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")

    response = test_client.patch(
        f"/api/v1/users/{user_uid}",
        json={"name": user_name, "email": user_email, "phone_number": user_phone, "role": role},
    )

    assert response.status_code == expected_status

    gcp_user_uid = response.json().get("context", {}).get("uid")
    assert gcp_user_uid is not None

    # User has been updated anyway in local DB.
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
def test_delete_gcp_user(test_client, test_db_session, sql_factory, user_uid, expected_status):
    gcp_user = sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")
    user_client = sql_factory.client_user.create(user=gcp_user)
    test_db_session.commit()

    response = test_client.delete(f"/api/v1/users/{user_uid}")

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_204_NO_CONTENT:
        assert test_db_session.scalar(select(func.count()).select_from(GCPUser)) == 0
        # Check that user Client is still there.
        assert (
            test_db_session.scalar(
                select(func.count()).select_from(Client).filter_by(uid=user_client.client_uid)
            )
            == 1
        )
