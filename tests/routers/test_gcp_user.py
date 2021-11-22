import pytest

from fastapi import status
from sqlalchemy import func, select

from user_management.models import Client, GCPUser


@pytest.mark.parametrize(
    ["user_name", "user_email", "user_phone", "expected_status"],
    [
        pytest.param(
            "",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user creation - No user name",
        ),
        pytest.param(
            "John Doe",
            "",
            "+4402081232389",
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user creation - No user email",
        ),
        pytest.param(
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            status.HTTP_409_CONFLICT,
            id="Wrong user creation - Duplicated user email",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "+4402081232389",
            status.HTTP_201_CREATED,
            id="Successful new user creation",
        ),
        pytest.param(
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "",
            status.HTTP_201_CREATED,
            id="Successful new user creation - no phone number required",
        ),
    ],
)
def test_create_client(
    test_client, test_db_session, sql_factory, user_name, user_email, user_phone, expected_status
):
    sql_factory.gcp_user.create(email="john.doe@hummingbirdtech.com")

    response = test_client.post(
        "/api/v1/users", json={"name": user_name, "email": user_email, "phone_number": user_phone}
    )

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_201_CREATED:
        gcp_user_uid = response.json()["uid"]
        gcp_user = test_db_session.get(GCPUser, gcp_user_uid)
        assert gcp_user.name == user_name
        assert gcp_user.email == user_email
        assert gcp_user.phone_number == user_phone


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
    gcp_user = sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")

    response = test_client.get(f"/api/v1/users/{user_uid}")

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_200_OK:
        expected = {
            "uid": str(gcp_user.uid),
            "name": gcp_user.name,
            "email": gcp_user.email,
            "phone_number": gcp_user.phone_number,
        }
        assert response.json() == expected


def test_list_gcp_users(test_client, sql_factory):
    gcp_users = sql_factory.gcp_user.create_batch(size=3)

    response = test_client.get("/api/v1/users")

    assert response.status_code == status.HTTP_200_OK
    expected = [
        {
            "uid": str(gcp_user.uid),
            "name": gcp_user.name,
            "email": gcp_user.email,
            "phone_number": gcp_user.phone_number,
        }
        for gcp_user in gcp_users
    ]
    assert response.json() == expected


@pytest.mark.parametrize(
    ["user_uid", "user_name", "user_email", "user_phone", "expected_status"],
    [
        pytest.param(
            "a0723fb5-6b0f-45ec-a131-6a6a1bd87741",
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            status.HTTP_404_NOT_FOUND,
            id="Wrong user update - Non existent user UID",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "John Doe",
            "",
            "+4402081232389",
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user update - No user email",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            status.HTTP_400_BAD_REQUEST,
            id="Wrong user update - No user name",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "Jane Doe",
            "jane.doe@hummingbirdtech.com",
            "+4402081232389",
            status.HTTP_409_CONFLICT,
            id="Wrong user update - Duplicating existent user email",
        ),
        pytest.param(
            "d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc",
            "John Doe",
            "john.doe@hummingbirdtech.com",
            "+4402081232389",
            status.HTTP_200_OK,
            id="Successful user update",
        ),
    ],
)
def test_update_gcp_user(
    test_client,
    test_db_session,
    sql_factory,
    user_uid,
    user_name,
    user_email,
    user_phone,
    expected_status,
):
    sql_factory.gcp_user.create(uid="d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc")
    sql_factory.gcp_user.create(email="jane.doe@hummingbirdtech.com")

    response = test_client.post(
        f"/api/v1/users/{user_uid}",
        json={"name": user_name, "email": user_email, "phone_number": user_phone},
    )

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_200_OK:
        modified_user = test_db_session.get(GCPUser, user_uid)
        assert modified_user.name == user_name
        assert modified_user.email == user_email
        assert modified_user.phone_number == user_phone


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
