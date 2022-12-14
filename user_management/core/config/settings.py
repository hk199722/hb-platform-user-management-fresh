from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, DirectoryPath, HttpUrl, PostgresDsn, SecretStr
from pydantic.schema import Pattern


class DBSettings(BaseSettings):
    database_url: PostgresDsn
    database_pool_size: int = 40
    database_max_overflow: int = 10
    database_pool_recycle: int = 3600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings(DBSettings):
    debug: bool = True
    google_project_id: str
    project_root: DirectoryPath = Path(__file__).resolve().parent.parent.parent.parent

    # Platform services
    accounts_base_url: HttpUrl

    # CORS middleware
    cors_allow_origins: Optional[Pattern]

    # GCP Identity Platform
    gcp_api_key: SecretStr
    gcp_credentials: Optional[SecretStr]
    gcp_request_timeout: int = 30

    # GCP Pub/Sub configuration
    topic_name: str = "mailing"
    message_limit: int = 500
    byte_limit: int = 2 * 1024 * 1024  # Max size in bytes of the total awaiting messages.

    # Sentry
    sentry_dsn: Optional[HttpUrl]
    release: Optional[str]

    # API tokens security
    encrypt_salt: SecretStr


@lru_cache(maxsize=1)
def get_settings():
    return Settings()
