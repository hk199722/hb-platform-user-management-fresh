from fastapi import APIRouter

from user_management.core.config.settings import get_settings


router = APIRouter()


@router.get("/test")
def test_sentry():
    import requests

    response = requests.get("https://sentry.io")
    if response != 200:
        raise ConnectionError("Sentry connection error.")

    raise Exception(
        f"Testing Sentry: {get_settings().sentry_dsn}; {get_settings().release}; {get_settings().google_project_id}."
    )
