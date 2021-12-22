import base64
import functools
import json
import os
from collections import namedtuple
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
from user_management.models import Role
from tests.factories import SQLModelFactory


RequestUser = namedtuple("RequestUser", ["user", "client_1", "client_2", "header_payload"])


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
    session_factory = sessionmaker(autoflush=True, bind=engine)
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


@pytest.fixture(name="sql_factory")
def sql_factory_init(test_db_session) -> Generator[SQLModelFactory, None, None]:
    """Makes SQL models factories available in tests."""
    yield SQLModelFactory.initialize(test_db_session)


@pytest.fixture
def user_info(sql_factory) -> Generator[RequestUser, None, None]:
    """GCP API Gateway 'X-Apigateway-Api-Userinfo' HTTP header value. To authenticate/authorize user
    in tests requiring API calls.

    Usage:

        def test_auth(test_client, user_info):
            response = test_client.get(
                "/api/v1/users",
                headers={"X-Apigateway-Api-Userinfo": user_info.header_payload}
            )
            assert response.status_code == 200

    The returned object contains also the `GCPUser` and the 2 `Client.uid`s she's related to, for
    convenience.
    """
    gcp_user = sql_factory.gcp_user.create(name="Request User")
    client_user_1 = sql_factory.client_user.create(user=gcp_user, role=Role.SUPERUSER)
    client_user_2 = sql_factory.client_user.create(user=gcp_user, role=Role.NORMAL_USER)
    timestamp = int(time())

    gcp_user_info = {
        "name": gcp_user.name,
        "roles": {
            str(client_user_1.client_uid): client_user_1.role.value,
            str(client_user_2.client_uid): client_user_2.role.value,
        },
        "iss": "https://securetoken.google.com/hbt-staging",
        "aud": "hbt-staging",
        "auth_time": timestamp,
        "user_id": str(gcp_user.uid),
        "sub": str(gcp_user.uid),
        "iat": timestamp,
        "exp": timestamp + 3600,
        "email": gcp_user.email,
        "email_verified": True,
        "firebase": {
            "identities": {"email": [gcp_user.email]},
            "sign_in_provider": "password",
        },
        "uid": str(gcp_user.uid),
    }

    payload = base64.b64encode(json.dumps(gcp_user_info).encode()).decode()

    yield RequestUser(
        user=gcp_user,
        client_1=client_user_1.client,
        client_2=client_user_2.client,
        header_payload=payload,
    )


@pytest.fixture
def staff_user_info(sql_factory) -> Generator[RequestUser, None, None]:
    """GCP API Gateway 'X-Apigateway-Api-Userinfo' HTTP header value. To authenticate/authorize user
    in tests requiring API calls.

    Similar to `user_info` fixture, but it delivers a HB Staff user.
    """
    gcp_user = sql_factory.gcp_user.create(name="Request User", staff=True)

    timestamp = int(time())

    staff_gcp_user_info = {
        "name": gcp_user.name,
        "staff": gcp_user.staff,
        "iss": "https://securetoken.google.com/hbt-staging",
        "aud": "hbt-staging",
        "auth_time": timestamp,
        "user_id": str(gcp_user.uid),
        "sub": str(gcp_user.uid),
        "iat": timestamp,
        "exp": timestamp + 3600,
        "email": gcp_user.email,
        "email_verified": True,
        "firebase": {
            "identities": {"email": [gcp_user.email]},
            "sign_in_provider": "password",
        },
        "uid": str(gcp_user.uid),
    }

    payload = base64.b64encode(json.dumps(staff_gcp_user_info).encode()).decode()

    yield RequestUser(user=gcp_user, client_1=None, client_2=None, header_payload=payload)
