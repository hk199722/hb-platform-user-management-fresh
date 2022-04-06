from fastapi import APIRouter

from user_management.core.config.settings import get_settings


router = APIRouter()


@router.get("/test")
def test_sentry():
    raise Exception(
        f"Testing Sentry: {get_settings().sentry_dsn}; {get_settings().release}; {get_settings().google_project_id}."
    )
