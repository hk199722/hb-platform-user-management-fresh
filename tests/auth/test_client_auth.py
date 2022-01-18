from fastapi import status


def test_get_client_unauthorized(test_client, user_info, sql_factory):
    """Users that are not HB Staff members can't see clients they are not assigned to."""
    client = sql_factory.client.create()

    response = test_client.get(
        f"/api/v1/clients/{client.uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_client_staff(test_client, staff_user_info, sql_factory):
    """Staff users can see all clients, even if they are not members of them."""
    client = sql_factory.client.create()

    response = test_client.get(
        f"/api/v1/clients/{client.uid}",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
    )

    assert response.status_code == status.HTTP_200_OK

    expected = {"name": client.name, "uid": str(client.uid)}
    assert response.json() == expected
