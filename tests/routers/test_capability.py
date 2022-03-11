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
def test_create_client(
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
