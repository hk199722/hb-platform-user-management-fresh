from typing import Generator

from sqlalchemy.orm import scoped_session

from user_management.core.database import db_session_factory


def get_database() -> Generator[scoped_session, None, None]:
    session_factory = db_session_factory()
    db_session = scoped_session(session_factory)

    try:
        yield db_session
    finally:
        db_session.remove()
