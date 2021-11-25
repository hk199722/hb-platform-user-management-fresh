import json
import logging
from functools import cache
from typing import Optional

from firebase_admin import App, initialize_app
from firebase_admin.credentials import Certificate

from user_management.core.config.settings import get_settings


logger = logging.getLogger(__name__)


@cache
def init_identity_platform_app() -> Optional[App]:
    """Cached function to initialize GCP Identity Platform / Firebase app."""
    settings = get_settings()
    if not settings.gcp_credentials:
        logger.warning("GCP Identity Platform NOT connected: GCP credentials not configured.")
        return None

    try:
        gcp_credentials = Certificate(json.loads(settings.gcp_credentials.get_secret_value()))
    except Exception:  # pylint: disable=broad-except
        logger.exception("GCP Identity Platform NOT connected: invalid GCP credentials.")
        return None

    try:
        app = initialize_app(
            credential=gcp_credentials, options={"httpTimeout": settings.gcp_request_timeout}
        )
    except Exception:  # pylint: disable=broad-except
        logger.exception("GCP Identity Platform NOT connected: unable to initialize app.")
        return None

    logger.info("GCP Identity Platform / Firebase app initialized.")

    return app
