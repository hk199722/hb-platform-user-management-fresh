import pytest

from fastapi import status

from user_management.models import GCPUser


@pytest.mark.parametrize(
    ["user_name", "user_email", "user_phone", "expected_status"],
    [
        # No user name.
        pytest.param(
            "", "john.doe@hummingbirdtech.com", "+4402081232389", status.HTTP_400_BAD_REQUEST
        ),
        # No user email.
        pytest.param("John Doe", "", "+4402081232389", status.HTTP_400_BAD_REQUEST),
        # Existent user email.
        pytest.param(
            "John Doe", "john.doe@hummingbirdtech.com", "+4402081232389", status.HTTP_409_CONFLICT
        ),
        # Successful new user creation.
        pytest.param(
            "Jane Doe", "jane.doe@hummingbirdtech.com", "+4402081232389", status.HTTP_201_CREATED
        ),
        # Successful new user creation - no phone number required.
        pytest.param("Jane Doe", "jane.doe@hummingbirdtech.com", "", status.HTTP_201_CREATED),
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
        pytest.param("d7a9aa45-1737-419a-bf5c-c2a4ac5b60cc", status.HTTP_200_OK),
        pytest.param("47294de0-8999-49c1-add4-6f8ac833ea6d", status.HTTP_404_NOT_FOUND),
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
