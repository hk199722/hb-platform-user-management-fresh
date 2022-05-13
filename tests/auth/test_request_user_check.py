from fastapi import status


def test_api_gateway_base64_header(test_client):
    """Test `RequestUserCheck.get_user` method for an API Gateway security header known to be not
    compliant with Python's Base64 module.
    """
    response = test_client.get(
        "/api/v1/users",
        headers={
            "X-Apigateway-Api-Userinfo": "eyJuYW1lIjoiTXlyb3NsYXYgVGFudHN5dXJhIiwic3RhZmYiOnRydWUsInJvbGVzIjp7fSwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL2h1bW1pbmdiaXJkdGVjaC1wcm9kdWN0aW9uIiwiYXVkIjoiaHVtbWluZ2JpcmR0ZWNoLXByb2R1Y3Rpb24iLCJhdXRoX3RpbWUiOjE2NTIzNzI1MjEsInVzZXJfaWQiOiIwMjllZjAwNC1hNGJmLTQxM2ItOGU4MS0yYjUxOGM4NzE0Y2UiLCJzdWIiOiIwMjllZjAwNC1hNGJmLTQxM2ItOGU4MS0yYjUxOGM4NzE0Y2UiLCJpYXQiOjE2NTIzNzI1MjEsImV4cCI6MTY1MjM3NjEyMSwiZW1haWwiOiJteXJvc2xhdkBodW1taW5nYmlyZHRlY2guY29tIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbIm15cm9zbGF2QGh1bW1pbmdiaXJkdGVjaC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJwYXNzd29yZCJ9fQ"
        },
    )

    assert response.status_code == status.HTTP_200_OK
