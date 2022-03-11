from fastapi import status
from sqlalchemy import select

from user_management.models import Capability


def test_create_capability_unauthorized(test_client, user_info, test_db_session):
    """Platform clients users are not authorized to create new capabilities."""
    response = test_client.post(
        "/api/v1/capabilities",
        headers={"X-Apigateway-Api-Userinfo": user_info.header_payload},
        json={"name": "Crop Type"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert test_db_session.scalars(select(Capability).filter_by(name="Crop Type")).all() == []


def test_create_capability_authorized(test_client, staff_user_info, test_db_session):
    """HB Staff users can create new capabilities."""
    response = test_client.post(
        "/api/v1/capabilities",
        headers={"X-Apigateway-Api-Userinfo": staff_user_info.header_payload},
        json={"name": "Crop Type"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert test_db_session.scalar(select(Capability).filter_by(name="Crop Type")) is not None
