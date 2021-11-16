import pytest

from fastapi import status
from sqlalchemy import func, select

from user_management.models import Client, GCPUser


@pytest.mark.parametrize(
    ["client_name", "expected_status"],
    [
        pytest.param("", status.HTTP_400_BAD_REQUEST),
        pytest.param("VASS Logic Ltd.", status.HTTP_409_CONFLICT),
        pytest.param("New Client", status.HTTP_201_CREATED),
    ],
)
def test_create_client(test_client, test_db_session, sql_factory, client_name, expected_status):
    sql_factory.client.create(name="VASS Logic Ltd.")

    response = test_client.post("/api/v1/clients", json={"name": client_name})

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_201_CREATED:
        client_uid = response.json()["uid"]
        client = test_db_session.get(Client, client_uid)
        assert client.name == client_name


@pytest.mark.parametrize(
    ["client_uid", "expected_status"],
    [
        pytest.param("ac2ef360-0002-4a8b-bf9b-84b7cf779960", status.HTTP_204_NO_CONTENT),
        pytest.param("e72957e6-df6e-476b-af93-a1ae4610e72b", status.HTTP_404_NOT_FOUND),
    ],
)
def test_delete_client(test_client, test_db_session, sql_factory, client_uid, expected_status):
    client = sql_factory.client.create(uid="ac2ef360-0002-4a8b-bf9b-84b7cf779960")
    sql_factory.gcp_user.create_batch(size=3, clients=[client])
    test_db_session.commit()

    response = test_client.delete(f"/api/v1/clients/{client_uid}")

    if expected_status == status.HTTP_204_NO_CONTENT:
        # Check response status and that client users have been deleted.
        assert response.status_code == expected_status
        test_db_session.expire_all()
        assert test_db_session.scalar(select(func.count()).select_from(Client)) == 0
        assert test_db_session.scalar(select(func.count()).select_from(GCPUser)) == 0
