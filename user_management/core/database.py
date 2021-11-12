import functools

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from user_management.core.config.settings import get_settings


@functools.lru_cache(maxsize=1)
def db_session_factory() -> sessionmaker:
    """Sessions registry for PostgreSQL Farm Management database."""
    settings = get_settings()
    engine = create_engine(
        settings.database_uri,
        pool_pre_ping=True,
        pool_recycle=settings.database_pool_recycle,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )

    return sessionmaker(autocommit=False, autoflush=True, bind=engine)


Base = declarative_base()
