import uuid

import pytest

from fastapi import status

from user_management.models import ClientFarm


@pytest.mark.parametrize(
    ["client_uid", "farm_uid", "expected_status"],
    [
        # No Client uid.
        pytest.param("", str(uuid.uuid4()), status.HTTP_400_BAD_REQUEST),
        # No Farm uid.
        pytest.param("970b5da1-f1a1-4255-8394-452e9f4e1f5e", "", status.HTTP_400_BAD_REQUEST),
        # Non-existent Client uid.
        pytest.param(
            "4e50e22f-3692-4016-be50-0bbf5aaef651", str(uuid.uuid4()), status.HTTP_404_NOT_FOUND
        ),
        # Already existent Client-Farm relationship.
        pytest.param(
            "970b5da1-f1a1-4255-8394-452e9f4e1f5e",
            "4f8b2788-ae34-4a39-9d89-29f076303dcc",
            status.HTTP_409_CONFLICT,
        ),
        # Successful creation.
        pytest.param(
            "970b5da1-f1a1-4255-8394-452e9f4e1f5e", str(uuid.uuid4()), status.HTTP_201_CREATED
        ),
    ],
)
def test_create_client_farm(
    test_client, test_db_session, sql_factory, client_uid, farm_uid, expected_status
):
    # Create a Client and a Client-Farm relationship to test.
    client = sql_factory.client.create(uid="970b5da1-f1a1-4255-8394-452e9f4e1f5e")
    sql_factory.client_farm.create(client=client, farm_uid="4f8b2788-ae34-4a39-9d89-29f076303dcc")

    response = test_client.post(
        "/api/v1/client-farms", json={"client_uid": client_uid, "farm_uid": farm_uid}
    )

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_201_CREATED:
        client_farm = test_db_session.get(ClientFarm, farm_uid)
        assert str(client_farm.client_uid) == client_uid
