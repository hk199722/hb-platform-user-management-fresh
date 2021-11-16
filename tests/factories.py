import uuid

import factory
from sqlalchemy.orm import Session

from user_management.models import Client, ClientFarm, GCPUser


class BaseModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    """
    Implements a base class for our `SQLAlchemyModelFactory` implementing a `bind` classmethod which
    will return a class of the given model factory with the passed SQLAlchemy session, as needed by
    Factory Boy library.
    """

    class Meta:
        abstract = True

    @classmethod
    def bind(cls, session: Session):
        cls._meta.sqlalchemy_session = session
        return cls


class ClientFactory(BaseModelFactory):
    uid = factory.Sequence(lambda n: uuid.uuid4())
    name = factory.Sequence(lambda n: f"Client-{n}")

    class Meta:
        model = Client
        sqlalchemy_session_persistence = "commit"


class GCPUserFactory(BaseModelFactory):
    uid = factory.Sequence(lambda n: uuid.uuid4())
    name = factory.Sequence(lambda n: f"GCPUser-{n}")
    email = factory.Sequence(lambda n: f"user-{n}@hummingbirdtech.com")
    phone_number = "+44 020 8123 2389"

    class Meta:
        model = GCPUser
        sqlalchemy_session_persistence = "commit"

    @factory.post_generation
    def clients(self, create, extracted):
        if not create:
            return

        if extracted:
            for client in extracted:
                self.clients.append(client)  # pylint: disable=no-member


class ClientFarmFactory(BaseModelFactory):
    farm_uid = factory.Sequence(lambda n: uuid.uuid4())
    client = factory.SubFactory(ClientFactory)

    class Meta:
        model = ClientFarm
        sqlalchemy_session_persistence = "commit"


class SQLModelFactory:
    """
    Implements an object that, when instantiated via its `initialize` method, will automatically
    create attributes for any factory models "bound" to a session that we might pass to the class
    constructor.

    Therefore this can be used as a Pytest fixture, so we can pass it to tests and invoke model
    factories from its attributes, just using Factory Boy API.
    """

    client = None
    gcp_user = None
    client_farm = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def initialize(cls, session: Session):
        return cls(
            client=ClientFactory.bind(session),
            gcp_user=GCPUserFactory.bind(session),
            client_farm=ClientFarmFactory.bind(session),
        )
