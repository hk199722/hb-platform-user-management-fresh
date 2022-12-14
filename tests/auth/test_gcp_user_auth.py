from unittest.mock import patch

from fastapi import status
from sqlalchemy import select

from user_management.models import GCPUser, Role


@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
@patch("user_management.services.mailer.PublisherClient")
def test_create_gcp_user_success(mock_pubsub, mock_gcp_ip, test_client, user_info, test_db_session):
    """Users with a `SUPERUSER` role in a Client can create new users within that client."""
    mock_gcp_ip().sync_gcp_user.side_effect = None  # Mock out GCP-IP access.
    mock_pubsub().sync_gcp_user.side_effect = None  # Mock out GCP Pub/Sub.

    response = test_client.post(
        "/api/v1/users",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={
            "name": "John Doe",
            "email": "john.doe@hummingbirdtech.com",
            "phone_number": "+34658071353",
            "role": {"client_uid": str(user_info.client_1.uid), "role": Role.NORMAL_USER.value},
        },
    )

    assert response.status_code == status.HTTP_201_CREATED, response.json()

    data = response.json()
    new_gcp_user = test_db_session.scalar(select(GCPUser).filter_by(uid=data["uid"]))
    assert new_gcp_user is not None
    assert data["clients"] == [
        {"client_uid": str(user_info.client_1.uid), "role": Role.NORMAL_USER.value}
    ]


@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
@patch("user_management.services.mailer.PublisherClient")
def test_create_gcp_user_staff(
    mock_pubsub, mock_gcp_ip, test_client, staff_user_info, test_db_session, sql_factory
):
    """HB Staff users can always create users for every Client with no restrictions."""
    mock_gcp_ip().sync_gcp_user.side_effect = None  # Mock out GCP-IP access.
    mock_pubsub().sync_gcp_user.side_effect = None  # Mock out GCP Pub/Sub.
    client = sql_factory.client.create()

    response = test_client.post(
        "/api/v1/users",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
        json={
            "name": "John Doe",
            "email": "john.doe@hummingbirdtech.com",
            "phone_number": "+34658071353",
            "role": {"client_uid": str(client.uid), "role": Role.NORMAL_USER.value},
        },
    )

    assert response.status_code == status.HTTP_201_CREATED, response.json()

    data = response.json()
    new_gcp_user = test_db_session.scalar(select(GCPUser).filter_by(uid=data["uid"]))
    assert new_gcp_user is not None
    assert data["clients"] == [{"client_uid": str(client.uid), "role": Role.NORMAL_USER.value}]


@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
@patch("user_management.services.mailer.PublisherClient")
def test_create_gcp_user_staff_no_client(
    mock_pubsub, mock_gcp_ip, test_client, staff_user_info, test_db_session
):
    """HB Staff users can create users with no Clients related."""
    mock_gcp_ip().sync_gcp_user.side_effect = None  # Mock out GCP-IP access.
    mock_pubsub().sync_gcp_user.side_effect = None  # Mock out GCP Pub/Sub.

    response = test_client.post(
        "/api/v1/users",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
        json={
            "name": "John Doe",
            "email": "john.doe@hummingbirdtech.com",
            "phone_number": "+34658071353",
            # No `role` submitted at all.
        },
    )

    assert response.status_code == status.HTTP_201_CREATED, response.json()

    data = response.json()
    new_gcp_user = test_db_session.scalar(select(GCPUser).filter_by(uid=data["uid"]))
    assert new_gcp_user is not None
    assert data["clients"] == []


def test_create_gcp_user_unauthorized_client(test_client, user_info, sql_factory):
    """Normal users can't create users under Clients they are not members of."""
    client = sql_factory.client.create()

    response = test_client.post(
        "/api/v1/users",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={
            "name": "John Doe",
            "email": "john.doe@hummingbirdtech.com",
            "phone_number": "+34658071353",
            "role": {"client_uid": str(client.uid), "role": Role.NORMAL_USER.value},
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


def test_create_gcp_user_unauthorized_role(test_client, user_info):
    """Normal users can't create new users if they are not `SUPERUSER`s themselves."""
    response = test_client.post(
        "/api/v1/users",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={
            "name": "John Doe",
            "email": "john.doe@hummingbirdtech.com",
            "phone_number": "+34658071353",
            "role": {"client_uid": str(user_info.client_2.uid), "role": Role.NORMAL_USER.value},
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


def test_get_gcp_user_success(test_client, user_info, sql_factory):
    """Users can access other user data if they are members of the same Client."""
    client_user = sql_factory.client_user.create(client=user_info.client_2)

    response = test_client.get(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    expected = {
        "uid": str(client_user.user.uid),
        "name": client_user.user.name,
        "phone_number": client_user.user.phone_number,
        "email": client_user.user.email,
        "staff": client_user.user.staff,
        "clients": [{"client_uid": str(client_user.client_uid), "role": client_user.role.value}],
    }
    assert response.json() == expected


def test_get_gcp_user_staff(test_client, staff_user_info, sql_factory):
    """HB Staff users can access any random user data."""
    client_user = sql_factory.client_user.create()

    response = test_client.get(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    expected = {
        "uid": str(client_user.user.uid),
        "name": client_user.user.name,
        "phone_number": client_user.user.phone_number,
        "email": client_user.user.email,
        "staff": client_user.user.staff,
        "clients": [{"client_uid": str(client_user.client_uid), "role": client_user.role.value}],
    }
    assert response.json() == expected


def test_get_gcp_user_unauthorized(test_client, user_info, sql_factory):
    """Users can't access data of other users that are not members of the same Clients."""
    client_user = sql_factory.client_user.create()

    response = test_client.get(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
def test_update_gcp_user_success(mock_gcp_ip, test_client, user_info, sql_factory):
    """Users can update other users if they are `SUPERUSER` role in the same Client."""
    mock_gcp_ip().sync_gcp_user.side_effect = None  # Mock out GCP-IP access.
    client_user = sql_factory.client_user.create(client=user_info.client_1, role=Role.NORMAL_USER)

    patch_payload = {
        "name": "John Doe",
        "email": "john.doe@hummingbirdtech.com",
        "phone_number": "+34658071353",
        "role": {"client_uid": str(user_info.client_1.uid), "role": Role.SUPERUSER.value},
    }

    response = test_client.patch(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json=patch_payload,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()


@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
def test_update_gcp_user_staff(
    mock_gcp_ip, test_client, staff_user_info, test_db_session, sql_factory
):
    """HB Staff users can update any platform user."""
    mock_gcp_ip().sync_gcp_user.side_effect = None  # Mock out GCP-IP access.
    client = sql_factory.client.create()
    client_user = sql_factory.client_user.create()

    patch_payload = {
        "name": "John Doe",
        "email": "john.doe@hummingbirdtech.com",
        "phone_number": "+34658071353",
        "role": {"client_uid": str(client.uid), "role": Role.SUPERUSER.value},
    }

    response = test_client.patch(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
        json=patch_payload,
    )

    assert response.status_code == status.HTTP_200_OK, response.json()

    test_db_session.expire_all()
    gcp_user = test_db_session.get(GCPUser, client_user.gcp_user_uid)
    assert gcp_user.name == patch_payload["name"]
    assert gcp_user.email == patch_payload["email"]


def test_update_gcp_user_unauthorized_client(test_client, user_info, sql_factory, test_db_session):
    """A user can't update another user if it's not a member of the same Client."""
    client_user = sql_factory.client_user.create()

    patch_payload = {
        "name": "John Doe",
        "email": "john.doe@hummingbirdtech.com",
        "phone_number": "+34658071353",
        "role": {"client_uid": str(user_info.client_1.uid), "role": Role.NORMAL_USER.value},
    }

    response = test_client.patch(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json=patch_payload,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()

    test_db_session.expire_all()
    gcp_user = test_db_session.get(GCPUser, client_user.gcp_user_uid)
    assert gcp_user.name != patch_payload["name"]
    assert gcp_user.email != patch_payload["email"]
    assert gcp_user.clients == [client_user]


def test_update_gcp_user_unauthorized_role(test_client, user_info, sql_factory, test_db_session):
    """A user who is not a `SUPERUSER` can't update another user, even in the same Client."""
    client_user = sql_factory.client_user.create(client=user_info.client_2, role=Role.PILOT)

    patch_payload = {
        "name": "John Doe",
        "email": "john.doe@hummingbirdtech.com",
        "phone_number": "+34658071353",
        "role": {"client_uid": str(user_info.client_2.uid), "role": Role.NORMAL_USER.value},
    }

    response = test_client.patch(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json=patch_payload,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()

    test_db_session.expire_all()
    gcp_user = test_db_session.get(GCPUser, client_user.gcp_user_uid)
    assert gcp_user.name != patch_payload["name"]
    assert gcp_user.email != patch_payload["email"]


@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
def test_delete_gcp_user_success(mock_gcp_ip, test_client, user_info, sql_factory, test_db_session):
    """Users can delete other users if they are `SUPERUSER` role in the same Client."""
    mock_gcp_ip().remove_gcp_user.side_effect = None  # Mock out GCP-IP access.
    client_user = sql_factory.client_user.create(client=user_info.client_1)

    response = test_client.delete(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()
    assert test_db_session.scalar(select(GCPUser).filter_by(uid=client_user.gcp_user_uid)) is None


@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
def test_delete_gcp_user_staff(
    mock_gcp_ip, test_client, staff_user_info, sql_factory, test_db_session
):
    """HB Staff users can delete any user in the platform."""
    mock_gcp_ip().remove_gcp_user.side_effect = None  # Mock out GCP-IP access.
    client_user = sql_factory.client_user.create()

    response = test_client.delete(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()
    assert test_db_session.scalar(select(GCPUser).filter_by(uid=client_user.gcp_user_uid)) is None


def test_delete_gcp_user_unauthorized_client(test_client, user_info, sql_factory, test_db_session):
    """A user can't delete another user if it's not a member of the same Client."""
    client_user = sql_factory.client_user.create()

    response = test_client.delete(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()
    assert (
        test_db_session.scalar(select(GCPUser).filter_by(uid=client_user.gcp_user_uid))
        == client_user.user
    )


@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
def test_delete_gcp_user_unauthorized_role(
    mock_gcp_ip, test_client, user_info, sql_factory, test_db_session
):
    """A user who is not a `SUPERUSER` can't delete another user, even in the same Client."""
    mock_gcp_ip().remove_gcp_user.side_effect = None  # Mock out GCP-IP access.
    client_user = sql_factory.client_user.create(client=user_info.client_2)

    response = test_client.delete(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()
    assert (
        test_db_session.scalar(select(GCPUser).filter_by(uid=client_user.gcp_user_uid))
        == client_user.user
    )


# pylint: disable=unused-argument
@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
def test_update_role_success(mock_gcp_ip, test_client, user_info, sql_factory, test_db_session):
    """Users can update the role of other users if they are `SUPERUSER` role in the same Client."""
    client_user = sql_factory.client_user.create(client=user_info.client_1, role=Role.NORMAL_USER)

    response = test_client.patch(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={"role": {"client_uid": str(user_info.client_1.uid), "role": Role.PILOT.value}},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()

    test_db_session.expire_all()
    gcp_user = test_db_session.scalar(select(GCPUser).filter_by(uid=client_user.gcp_user_uid))
    assert len(gcp_user.clients) == 1
    assert gcp_user.clients[0].role == Role.NORMAL_USER


# pylint: disable=unused-argument
@patch("user_management.services.gcp_user.GCPIdentityPlatformService")
def test_update_role_staff(mock_gcp_ip, test_client, staff_user_info, sql_factory, test_db_session):
    """HB Staff users can change the roles of any user in the platform."""
    client_user = sql_factory.client_user.create(role=Role.PILOT)

    response = test_client.patch(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
        json={"role": {"client_uid": str(client_user.client_uid), "role": Role.NORMAL_USER.value}},
    )

    assert response.status_code == status.HTTP_200_OK, response.json()

    assert response.json()["clients"] == [
        {"client_uid": str(client_user.client_uid), "role": Role.NORMAL_USER.value}
    ]

    test_db_session.expire_all()
    gcp_user = test_db_session.scalar(select(GCPUser).filter_by(uid=client_user.gcp_user_uid))
    assert len(gcp_user.clients) == 1
    assigned_client = gcp_user.clients[0]
    assert assigned_client.client_uid == client_user.client_uid
    assert assigned_client.role == Role.NORMAL_USER


def test_update_role_unauthorized_role(test_client, user_info, sql_factory, test_db_session):
    """A user who is not a `SUPERUSER` can't update another user's role, even in the same Client."""
    client_user = sql_factory.client_user.create(client=user_info.client_2, role=Role.PILOT)

    response = test_client.patch(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={"role": {"client_uid": str(user_info.client_2.uid), "role": Role.NORMAL_USER.value}},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()

    test_db_session.expire_all()
    gcp_user = test_db_session.scalar(select(GCPUser).filter_by(uid=client_user.gcp_user_uid))
    assert len(gcp_user.clients) == 1
    assigned_client = gcp_user.clients[0]
    assert assigned_client.client_uid == client_user.client_uid
    assert assigned_client.role == client_user.role


def test_update_role_unauthorized_client(test_client, user_info, sql_factory, test_db_session):
    """A user can't delete another user if it's not a member of the same Client."""
    client_user = sql_factory.client_user.create(role=Role.PILOT)

    response = test_client.patch(
        f"/api/v1/users/{client_user.gcp_user_uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={"role": {"client_uid": str(client_user.client_uid), "role": Role.NORMAL_USER.value}},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()

    test_db_session.expire_all()
    gcp_user = test_db_session.scalar(select(GCPUser).filter_by(uid=client_user.gcp_user_uid))
    assert len(gcp_user.clients) == 1
    assigned_client = gcp_user.clients[0]
    assert assigned_client.client_uid == client_user.client_uid
    assert assigned_client.role == client_user.role
