import base64
import functools
import json
import os
from time import time
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import scoped_session, Session, sessionmaker

from user_management.core.database import Base
from user_management.core.dependencies import get_database
from user_management.core.config.settings import get_settings
from user_management.main import create_app
from tests.factories import SQLModelFactory


@functools.lru_cache
def get_database_name():
    settings = get_settings()
    return f"{settings.database_url.path.lstrip('/')}_test_{os.getpid()}"


def create_test_db_session(db_name: str, manager: bool = False) -> scoped_session:
    """
    Creates a database to be used by test fixtures. Database name will be the one defined in actual
    project settings, with `_test_<PROCESS_ID>` suffix, so it will support pytest parallelization.
    A testing DB will then be created for every pytest worker.
    """
    settings = get_settings()

    database_url = PostgresDsn.build(
        scheme="postgresql",
        user=settings.database_url.user,
        password=settings.database_url.password,
        host=settings.database_url.host,
        port=settings.database_url.port,
        path=f"/{db_name}" if manager is False else None,
    )

    engine = create_engine(database_url, pool_pre_ping=True)
    session_factory = sessionmaker(autocommit=False, autoflush=True, bind=engine)
    return scoped_session(session_factory)


def destroy_database(db_name):
    session = create_test_db_session(db_name=db_name, manager=True)
    with session.bind.connect() as man_connection:
        man_connection.execution_options(isolation_level="AUTOCOMMIT").execute(
            text(
                f"SELECT pg_terminate_backend(pg_stat_activity.pid) "
                f"FROM pg_stat_activity WHERE pg_stat_activity.datname = '{db_name}' "
                f"AND pid <> pg_backend_pid()"
            )
        )
        man_connection.execution_options(isolation_level="AUTOCOMMIT").execute(
            text(f'DROP DATABASE IF EXISTS "{db_name}"')
        )


def create_database(db_name: str):
    destroy_database(db_name)

    session = create_test_db_session(db_name=db_name, manager=True)
    with session.bind.connect() as man_connection:
        man_connection.execution_options(isolation_level="AUTOCOMMIT").execute(
            text(f"CREATE DATABASE {db_name}")
        )

    session = create_test_db_session(db_name=db_name)
    with session.bind.connect() as man_connection:
        man_connection.execution_options(isolation_level="AUTOCOMMIT").execute(
            text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        )


@pytest.fixture(scope="session", autouse=True, name="disposable_database")
def auto_disposable_database() -> Generator[Connection, None, None]:
    """
    Session wide fixture that creates a DB, or multiple DBs if running in parallel mode, and removes
    it at the end of tests session.

    Creates a database to be used by test fixtures. Database name will be the one defined in actual
    project settings, with `_test_<PROCESS_ID>` suffix, so it will support pytest parallelization.
    A testing DB will then be created for every pytest worker.

    To be used in another fixture where an existent DB session is created to be used as the real
    tests fixture. This one should not be passed to tests.
    """
    db_name = get_database_name()

    # Create the testing database.
    create_database(db_name)

    session = create_test_db_session(db_name)

    with session.bind.connect() as connection:
        Base.metadata.create_all(bind=connection)  # type: ignore
        yield connection
        Base.metadata.drop_all(bind=connection)  # type: ignore

    # Clean up cluster, drop testing database at the end of tests.
    destroy_database(db_name)


def override_get_database() -> Generator[scoped_session, None, None]:
    """
    Override function for the `get_database` FastAPI dependency, so the actual test database will be
    used instead of the app configured one.
    """
    ScopedSession = create_test_db_session(get_database_name())
    db_session = ScopedSession()

    try:
        yield db_session
    finally:
        db_session.close()


@pytest.fixture(scope="module")
def test_client() -> Generator[TestClient, None, None]:
    """Test client to be used to make API requests, when needed."""
    # Make sure our testing DB is used in the app too.
    app = create_app()
    app.dependency_overrides[get_database] = override_get_database

    yield TestClient(app)


@pytest.fixture(scope="function", name="test_db_session")
def testing_db_session(disposable_database: Connection) -> Generator[Session, None, None]:
    """
    Test DB session, automatically removes any data created in a test after test is ran. To be used
    in tests whenever access to DB is needed.
    """
    session_factory = sessionmaker(
        autocommit=False, bind=disposable_database.engine, expire_on_commit=False
    )
    session = session_factory()

    try:
        yield session
    except Exception:  # pylint: disable=broad-except
        session.rollback()
    finally:
        # In any case, cleanup the test database after every test to remove any
        # created data.
        meta = MetaData()
        meta.reflect(bind=disposable_database)
        session.expire_all()
        for table in meta.sorted_tables:
            session.execute(table.delete())

        session.commit()
        session.close()


@pytest.fixture
def sql_factory(test_db_session) -> Generator[SQLModelFactory, None, None]:
    """Makes SQL models factories available in tests."""
    yield SQLModelFactory.initialize(test_db_session)


@pytest.fixture
def test_user_info() -> Generator[str, None, None]:
    """GCP API Gateway 'X-Apigateway-Api-Userinfo' HTTP header value. To authenticate/authorize user
    in tests requiring API calls.
    """
    timestamp = int(time())

    # TODO: Add user claims to the next dictionary.
    user_info = {
        "name": "test_user@hummingbirdtech.com",
        "iss": "https://securetoken.google.com/hbt-staging",
        "aud": "hbt-staging",
        "auth_time": timestamp,
        "user_id": "1aaeaf8a-829e-45ac-a5f4-e6177633d62d",
        "sub": "1aaeaf8a-829e-45ac-a5f4-e6177633d62d",
        "iat": timestamp,
        "exp": timestamp + 3600,
        "email": "test_user@hummingbirdtech.com",
        "email_verified": True,
        "firebase": {
            "identities": {"email": ["test_user@hummingbirdtech.com"]},
            "sign_in_provider": "password",
        },
        "uid": "1aaeaf8a-829e-45ac-a5f4-e6177633d62d",
    }

    yield base64.b64encode(json.dumps(user_info).encode()).decode()
