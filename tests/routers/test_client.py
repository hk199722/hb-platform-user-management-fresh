from unittest.mock import patch

import pytest

from fastapi import status
from sqlalchemy import func, select

from user_management.models import Client, GCPUser, ClientUser


@pytest.mark.parametrize(
    ["client_name", "expected_status"],
    [
        pytest.param("", status.HTTP_400_BAD_REQUEST, id="Wrong client creation - No name"),
        pytest.param(
            "VASS Logic Ltd.",
            status.HTTP_409_CONFLICT,
            id="Wrong client creation - Duplicated name",
        ),
        pytest.param("New Client", status.HTTP_201_CREATED, id="Successful client creation"),
    ],
)
def test_create_client(
    test_client, user_info, test_db_session, sql_factory, client_name, expected_status
):
    sql_factory.client.create(name="VASS Logic Ltd.")

    response = test_client.post(
        "/api/v1/clients",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={"name": client_name},
    )

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_201_CREATED:
        client_uid = response.json()["uid"]
        client = test_db_session.get(Client, client_uid)
        assert client.name == client_name


@pytest.mark.parametrize(
    ["client_uid", "expected_status"],
    [
        pytest.param(
            "ac2ef360-0002-4a8b-bf9b-84b7cf779960",
            status.HTTP_200_OK,
            id="Successful client retrieval",
        ),
        pytest.param(
            "e72957e6-df6e-476b-af93-a1ae4610e72b",
            status.HTTP_404_NOT_FOUND,
            id="Non existent client UID",
        ),
    ],
)
def test_get_client(test_client, user_info, sql_factory, client_uid, expected_status):
    client = sql_factory.client.create(uid="ac2ef360-0002-4a8b-bf9b-84b7cf779960")

    response = test_client.get(
        f"/api/v1/clients/{client_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_200_OK:
        expected = {"name": client.name, "uid": client.uid}
        assert response.json() == expected


def test_list_clients(test_client, user_info, sql_factory):
    # Create 3 Clients that the request user has been assigned to. This will be shown in response.
    client_users = sql_factory.client_user.create_batch(size=3, user=user_info.user)
    # Create 3 other Clients the request user is not related to. This will NOT be shown.
    sql_factory.client.create_batch(size=3)

    response = test_client.get(
        "/api/v1/clients", headers={"X-Apigateway-Api-Userinfo": user_info.header_payload}
    )

    assert response.status_code == status.HTTP_200_OK

    # The clients we created above for the user...
    expected = [
        {"name": client_user.client.name, "uid": str(client_user.client.uid)}
        for client_user in client_users
    ]
    # ...and the ones the user already belong, from conftest.
    expected.extend(
        [
            {"name": user_info.client_1.name, "uid": str(user_info.client_1.uid)},
            {"name": user_info.client_2.name, "uid": str(user_info.client_2.uid)},
        ]
    )
    assert len(response.json()) == 5
    for client in response.json():
        assert client in expected


@pytest.mark.parametrize(
    ["client_uid", "expected_status"],
    [
        pytest.param(
            "ac2ef360-0002-4a8b-bf9b-84b7cf779960",
            status.HTTP_204_NO_CONTENT,
            id="Successful client deletion",
        ),
        pytest.param(
            "e72957e6-df6e-476b-af93-a1ae4610e72b",
            status.HTTP_404_NOT_FOUND,
            id="Non existent client UID",
        ),
    ],
)
@patch("user_management.services.gcp_identity.delete_users")
def test_delete_client(
    mock_identity_platform,  # pylint: disable=unused-argument
    test_client,
    staff_user_info,
    test_db_session,
    sql_factory,
    client_uid,
    expected_status,
):
    # Create a Client and assign 3 GCPUsers.
    client = sql_factory.client.create(uid="ac2ef360-0002-4a8b-bf9b-84b7cf779960")
    client_users = sql_factory.client_user.create_batch(size=3, client=client)

    # Now, create 2 more GCPUsers and assign it to the initial Client:
    # - One is a regular user, and is also assigned to another Client.
    # - Other is an HB Staff user, and it is assigned only to the initial Client.
    gcp_user = sql_factory.gcp_user.create()
    staff_gcp_user = sql_factory.gcp_user.create(staff=True)
    new_client_user = sql_factory.client_user.create(user=gcp_user)
    sql_factory.client_user.create(client=client, user=gcp_user)  # Initial Client.
    sql_factory.client_user.create(client=client, user=staff_gcp_user)  # Initial Client.
    test_db_session.commit()

    response = test_client.delete(
        f"/api/v1/clients/{client_uid}",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
    )

    # We deleted `client`, which had 4 users.
    assert response.status_code == expected_status
    if expected_status == status.HTTP_204_NO_CONTENT:
        # Check that client users have been deleted...
        assert (
            test_db_session.scalar(
                select(func.count()).select_from(Client).filter_by(uid=client.uid)
            )
            == 0
        )
        assert (
            test_db_session.scalar(
                select(func.count()).select_from(ClientUser).filter_by(client=client)
            )
            == 0
        )
        # ...except the one created last, which also belongs to another Client, so it must remain.
        assert (
            test_db_session.scalar(
                select(func.count())
                .select_from(ClientUser)
                .filter_by(client=new_client_user.client)
            )
            == 1
        )

        # GCPUsers from `client` that didn't belong to any other Client have been removed from the
        # system (3 in total). The one that belonged to another Client and the staff user remains.
        assert (
            test_db_session.scalar(
                select(func.count())
                .select_from(GCPUser)
                .filter(GCPUser.uid.in_([n.gcp_user_uid for n in client_users]))
            )
            == 0
        )

        assert test_db_session.scalar(select(GCPUser).filter_by(uid=gcp_user.uid))
        assert test_db_session.scalar(select(GCPUser).filter_by(uid=staff_gcp_user.uid))


@pytest.mark.parametrize(
    ["client_uid", "new_name", "expected_status"],
    [
        pytest.param(
            "ac2ef360-0002-4a8b-bf9b-84b7cf779960",
            "VASS Logic Ltd.",
            status.HTTP_200_OK,
            id="Successful client update",
        ),
        pytest.param(
            "ac2ef360-0002-4a8b-bf9b-84b7cf779960",
            "",
            status.HTTP_400_BAD_REQUEST,
            id="Wrong client update - No name",
        ),
        pytest.param(
            "ac2ef360-0002-4a8b-bf9b-84b7cf779960",
            "Fields Ltd.",
            status.HTTP_409_CONFLICT,
            id="Wrong client update - Duplicated name.",
        ),
        pytest.param(
            "e72957e6-df6e-476b-af93-a1ae4610e72b",
            "Client",
            status.HTTP_404_NOT_FOUND,
            id="Non existent client UID",
        ),
    ],
)
def test_update_client(
    test_client, user_info, test_db_session, sql_factory, client_uid, new_name, expected_status
):
    sql_factory.client.create(name="AgroCorp", uid="ac2ef360-0002-4a8b-bf9b-84b7cf779960")
    sql_factory.client.create(name="Fields Ltd.")

    response = test_client.patch(
        f"/api/v1/clients/{client_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={"name": new_name},
    )

    assert response.status_code == expected_status
    if expected_status == status.HTTP_200_OK:
        assert response.json().get("name") == new_name

        modified_client = test_db_session.get(Client, client_uid)
        assert modified_client.name == new_name
