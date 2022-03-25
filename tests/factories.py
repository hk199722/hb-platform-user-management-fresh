import random
import uuid

import factory
from factory import fuzzy
from sqlalchemy.orm import Session

from user_management.models import (
    Capability,
    Client,
    ClientAPIToken,
    ClientCapability,
    ClientUser,
    GCPUser,
    Role,
    SecurityToken,
)


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
    email = factory.LazyAttribute(
        lambda o: f"{o.name.lower().replace(' ', '-')}@hummingbirdtech.com"
    )
    phone_number = factory.LazyFunction(lambda: f"+44{random.randint(2000000000,3999999999)}")

    class Meta:
        model = GCPUser
        sqlalchemy_session_persistence = "commit"


class ClientUserFactory(BaseModelFactory):
    user = factory.SubFactory(GCPUserFactory)
    client = factory.SubFactory(ClientFactory)
    role = fuzzy.FuzzyChoice([role for role in Role])

    class Meta:
        model = ClientUser
        sqlalchemy_session_persistence = "commit"


class SecurityTokenFactory(BaseModelFactory):
    uid = factory.Sequence(lambda n: uuid.uuid4())
    user = factory.SubFactory(GCPUserFactory)

    class Meta:
        model = SecurityToken
        sqlalchemy_session_persistence = "commit"


class CapabilityFactory(BaseModelFactory):
    name = factory.Sequence(lambda n: f"Capability-{n}")

    class Meta:
        model = Capability
        sqlalchemy_session_persistence = "commit"


class ClientCapabilityFactory(BaseModelFactory):
    capability = factory.SubFactory(CapabilityFactory)
    client = factory.SubFactory(ClientFactory)

    class Meta:
        model = ClientCapability
        sqlalchemy_session_persistence = "commit"


class ClientAPITokenFactory(BaseModelFactory):
    client = factory.SubFactory(ClientFactory)
    token = factory.fuzzy.FuzzyText(length=40)

    class Meta:
        model = ClientAPIToken
        sqlalchemy_session_persistence = "commit"


class SQLModelFactory:
    """
    Implements an object that, when instantiated via its `initialize` method, will automatically
    create attributes for any factory models "bound" to a session that we might pass to the class
    constructor.

    Therefore, this can be used as a Pytest fixture, so we can pass it to tests and invoke model
    factories from its attributes, just using Factory Boy API.
    """

    capability = None
    client = None
    client_api_token = None
    client_capability = None
    client_user = None
    gcp_user = None
    security_token = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def initialize(cls, session: Session):
        return cls(
            client=ClientFactory.bind(session),
            capability=CapabilityFactory.bind(session),
            client_api_token=ClientAPITokenFactory.bind(session),
            client_capability=ClientCapabilityFactory.bind(session),
            gcp_user=GCPUserFactory.bind(session),
            client_user=ClientUserFactory.bind(session),
            security_token=SecurityTokenFactory.bind(session),
        )
