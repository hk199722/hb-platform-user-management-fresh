from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = False

    # Add here more project configuration settings, as needed.

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings():
    return Settings()
