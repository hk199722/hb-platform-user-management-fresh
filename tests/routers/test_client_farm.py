import uuid

import pytest

from fastapi import status
from sqlalchemy import func, select

from user_management.models import Client, ClientFarm


@pytest.mark.parametrize(
    ["client_uid", "farm_uid", "expected_status"],
    [
        pytest.param(
            "",
            str(uuid.uuid4()),
            status.HTTP_400_BAD_REQUEST,
            id="Wrong client farm creation - No client UID",
        ),
        pytest.param(
            "970b5da1-f1a1-4255-8394-452e9f4e1f5e",
            "",
            status.HTTP_400_BAD_REQUEST,
            id="Wrong client farm creation - No farm UID",
        ),
        pytest.param(
            "4e50e22f-3692-4016-be50-0bbf5aaef651",
            str(uuid.uuid4()),
            status.HTTP_404_NOT_FOUND,
            id="Wrong client farm creation - Non existent client UID",
        ),
        pytest.param(
            "970b5da1-f1a1-4255-8394-452e9f4e1f5e",
            "4f8b2788-ae34-4a39-9d89-29f076303dcc",
            status.HTTP_409_CONFLICT,
            id="Wrong client farm creation - Duplicated Client-Farm relationship",
        ),
        pytest.param(
            "970b5da1-f1a1-4255-8394-452e9f4e1f5e",
            str(uuid.uuid4()),
            status.HTTP_201_CREATED,
            id="Successful client farm creation",
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


@pytest.mark.parametrize(
    ["farm_uid", "expected_status"],
    [
        pytest.param(
            "4f8b2788-ae34-4a39-9d89-29f076303dcc",
            status.HTTP_200_OK,
            id="Successful client farm detail retrieval",
        ),
        pytest.param(
            str(uuid.uuid4()),
            status.HTTP_404_NOT_FOUND,
            id="Wrong client farm retrieval - Non existent client farm UID",
        ),
    ],
)
def test_get_client_farm(test_client, sql_factory, farm_uid, expected_status):
    client_farm = sql_factory.client_farm.create(farm_uid="4f8b2788-ae34-4a39-9d89-29f076303dcc")

    response = test_client.get(f"/api/v1/client-farms/{farm_uid}")

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_200_OK:
        expected = {"client_uid": str(client_farm.client_uid), "farm_uid": str(farm_uid)}
        assert response.json() == expected


def test_list_client_farms(test_client, sql_factory):
    client_farms = sql_factory.client_farm.create_batch(size=3)

    response = test_client.get("/api/v1/client-farms")

    assert response.status_code == status.HTTP_200_OK
    expected = [
        {"client_uid": str(client_farm.client_uid), "farm_uid": str(client_farm.farm_uid)}
        for client_farm in client_farms
    ]
    assert response.json() == expected


@pytest.mark.parametrize(
    ["farm_uid", "expected_status"],
    [
        pytest.param(
            str(uuid.uuid4()), status.HTTP_404_NOT_FOUND, id="Successful client farm deletion"
        ),
        pytest.param(
            "4f8b2788-ae34-4a39-9d89-29f076303dcc",
            status.HTTP_204_NO_CONTENT,
            id="Wrong client farm deletion - Non existent client farm UID",
        ),
    ],
)
def test_delete_client_farm(test_client, test_db_session, sql_factory, farm_uid, expected_status):
    client_farm = sql_factory.client_farm.create(farm_uid="4f8b2788-ae34-4a39-9d89-29f076303dcc")

    response = test_client.delete(f"/api/v1/client-farms/{farm_uid}")

    assert response.status_code == expected_status
    if expected_status == status.HTTP_204_NO_CONTENT:
        assert test_db_session.scalar(select(func.count()).select_from(ClientFarm)) == 0
        # Client remains here, only its relationship with a Farm has been removed.
        assert (
            test_db_session.scalar(
                select(func.count()).select_from(Client).filter_by(uid=client_farm.client_uid)
            )
            == 1
        )
