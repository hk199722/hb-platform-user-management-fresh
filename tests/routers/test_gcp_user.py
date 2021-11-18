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
