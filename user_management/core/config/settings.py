from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, DirectoryPath, PostgresDsn, SecretStr
from pydantic.schema import Pattern


class Settings(BaseSettings):
    debug: bool = False
    project_root: DirectoryPath = Path(__file__).resolve().parent.parent.parent.parent

    # Database
    database_url: PostgresDsn
    database_pool_size: int = 40
    database_max_overflow: int = 10
    database_pool_recycle: int = 3600

    # CORS middleware
    cors_allow_origins: Optional[Pattern]

    # GCP Identity Platform
    gcp_credentials: Optional[SecretStr]
    gcp_request_timeout: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings():
    return Settings()
