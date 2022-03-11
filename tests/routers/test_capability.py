import pytest

from fastapi import status

from user_management.models import Capability


@pytest.mark.parametrize(
    ["capability_name", "expected_status"],
    [
        pytest.param("", status.HTTP_400_BAD_REQUEST, id="Wrong capability creation - No name"),
        pytest.param(
            "Cover Crops",
            status.HTTP_409_CONFLICT,
            id="Wrong capability creation - Duplicated name",
        ),
        pytest.param("Tillage", status.HTTP_201_CREATED, id="Successful capability creation"),
    ],
)
def test_create_capability(
    test_client, staff_user_info, test_db_session, sql_factory, capability_name, expected_status
):
    sql_factory.capability.create(name="Cover Crops")

    response = test_client.post(
        "/api/v1/capabilities",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
        json={"name": capability_name},
    )

    assert response.status_code == expected_status
    if response.status_code == status.HTTP_201_CREATED:
        capability_id = response.json()["id"]
        capability = test_db_session.get(Capability, capability_id)
        assert capability.name == capability_name


def test_get_capability_non_existing(test_client, user_info):
    response = test_client.get(
        "/api/v1/capabilities/9999999999",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_capability_success(test_client, user_info, sql_factory):
    capability = sql_factory.capability.create()
    response = test_client.get(
        f"/api/v1/capabilities/{capability.id}",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": capability.id, "name": capability.name}


def test_get_capabilities(test_client, user_info, sql_factory):
    capability_1 = sql_factory.capability.create(name="Cover Crops")
    capability_2 = sql_factory.capability.create(name="Crop Type")
    capability_3 = sql_factory.capability.create(name="Tillage")

    response = test_client.get(
        "/api/v1/capabilities",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert response.json() == [
        {"id": capability_1.id, "name": capability_1.name},
        {"id": capability_2.id, "name": capability_2.name},
        {"id": capability_3.id, "name": capability_3.name},
    ]
