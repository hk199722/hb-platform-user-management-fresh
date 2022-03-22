import pytest

from fastapi import status
from sqlalchemy import func, select

from user_management.models import Capability, ClientCapability


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


@pytest.mark.parametrize(
    ["client_uid", "capability_id", "expected_response_status", "expected_response_message"],
    [
        pytest.param(
            "4715c934-c2f1-4fd6-a1b7-1b5be21f7f55",
            99,
            status.HTTP_204_NO_CONTENT,
            None,
            id="Successfully enabled capability for Client",
        ),
        pytest.param(
            "ebf78ecb-cd6a-455d-8214-f69d3bd0d152",
            99,
            status.HTTP_400_BAD_REQUEST,
            {
                "app_exception": "RequestError",
                "context": {"message": "Invalid Capability ID or Client UUID."},
            },
            id="Wrong capability enabling - Client UUID does not exist.",
        ),
        pytest.param(
            "4715c934-c2f1-4fd6-a1b7-1b5be21f7f55",
            999999999,
            status.HTTP_400_BAD_REQUEST,
            {
                "app_exception": "RequestError",
                "context": {"message": "Invalid Capability ID or Client UUID."},
            },
            id="Wrong capability enabling - Capability ID does not exist.",
        ),
        pytest.param(
            "91e28177-1bb2-4e32-9ba7-4d73e9ecdb53",
            99,
            status.HTTP_409_CONFLICT,
            {
                "app_exception": "ResourceConflictError",
                "context": {"message": "Selected Capability is already enabled for client."},
            },
            id="Wrong capability enabling - Client already has selected capability enabled.",
        ),
    ],
)
def test_enable_capability(
    test_client,
    staff_user_info,
    sql_factory,
    test_db_session,
    client_uid,
    capability_id,
    expected_response_status,
    expected_response_message,
):
    capability = sql_factory.capability.create(id=99)
    sql_factory.client.create(uid="4715c934-c2f1-4fd6-a1b7-1b5be21f7f55")
    sql_factory.client_capability.create(
        client__uid="91e28177-1bb2-4e32-9ba7-4d73e9ecdb53", capability=capability
    )

    response = test_client.post(
        "/api/v1/capabilities/enable",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
        json={"client_uid": client_uid, "capability_id": capability_id},
    )

    assert response.status_code == expected_response_status, response.json()

    if expected_response_status == status.HTTP_204_NO_CONTENT:
        # Check that the `ClientCapability` was properly created.
        assert (
            test_db_session.scalar(
                select(func.count())
                .select_from(ClientCapability)
                .filter_by(client_uid=client_uid, capability_id=capability_id)
            )
            == 1
        )

    if expected_response_status == status.HTTP_400_BAD_REQUEST:
        assert response.json() == expected_response_message
        # Check that the wrong data was not persisted in DB.
        assert (
            test_db_session.scalar(
                select(func.count())
                .select_from(ClientCapability)
                .filter_by(client_uid=client_uid, capability_id=capability_id)
            )
            == 0
        )
