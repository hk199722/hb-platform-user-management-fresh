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

    expected = {"name": client.name, "uid": str(client.uid), "callback_url": str(client.callback_url)}
    assert response.json() == expected


def test_update_client_unauthorized(test_client, user_info):
    """Users cannot update a Client, even when they are `SUPERUSER` in that client."""
    response = test_client.patch(
        f"/api/v1/clients/{user_info.client_1.uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={"name": "VASS Logic Ltd."},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_client_staff(test_client, staff_user_info, sql_factory):
    """Staff users can update any client."""
    client = sql_factory.client.create(name="Fields Ltd.")

    response = test_client.patch(
        f"/api/v1/clients/{client.uid}",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
        json={"name": "MegaCorp Ltd."},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("name") == "MegaCorp Ltd."


def test_delete_client_unauthorized(test_client, user_info):
    """Users cannot delete a Client, even when they are `SUPERUSER` in that client."""
    response = test_client.delete(
        f"/api/v1/clients/{user_info.client_1.uid}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_client_staff(test_client, staff_user_info, sql_factory):
    """Staff users can delete any client."""
    client = sql_factory.client.create()

    response = test_client.delete(
        f"/api/v1/clients/{client.uid}",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_generate_api_token_unauthorized(test_client, user_info):
    """Users cannot generate API tokens for clients they don't belong to."""
    response = test_client.get(
        "/api/v1/clients/2299be00-914a-4efa-96db-0892d9059138/api-token",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()


def test_generate_api_token_staff(test_client, staff_user_info, sql_factory):
    """Staff users can generate tokens for any Client, with no restrictions."""
    client = sql_factory.client.create()

    response = test_client.get(
        f"/api/v1/clients/{client.uid}/api-token",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
    )

    assert response.status_code == status.HTTP_200_OK, response.json()


def test_generate_api_token_staff_does_not_exist(test_client, staff_user_info):
    """Test backend response when a Staff user tries to generate a token for a non-existing client."""
    response = test_client.get(
        "/api/v1/clients/2299be00-914a-4efa-96db-0892d9059138/api-token",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
    assert response.json() == {
        "app_exception": "RequestError",
        "context": {"message": "Invalid Client UUID."},
    }
