import pytest
import types

from pydantic import BaseModel

from user_management.models import Client
from user_management.repositories.base import AlchemyRepository


class DummySchema(BaseModel):
    """Dummy Pydantic schema to be used in `AlchemyRepository` class tests."""

    field_1: str
    field_2: int


def test_subclass_alchemy_repository_missing_model():
    """Any class subclassing `AlchemyRepository` must specify a `model`."""
    namespace = {"schema": DummySchema}

    with pytest.raises(AssertionError, match="`model` attribute must be set."):
        types.new_class(
            "TestingRepository",
            bases=(AlchemyRepository,),
            exec_body=lambda ns: ns.update(namespace),
        )


def test_subclass_alchemy_repository_wrong_model():
    """The `model` attribute must be of the correct type."""
    namespace = {"model": int, "schema": DummySchema}

    with pytest.raises(TypeError, match="`model` attribute must be a SQLAlchemy model."):
        types.new_class(
            "TestingRepository",
            bases=(AlchemyRepository,),
            exec_body=lambda ns: ns.update(namespace),
        )


def test_subclass_alchemy_repository_missing_schema():
    """Any class subclassing `AlchemyRepository` must specify a `schema`."""
    namespace = {"model": Client}

    with pytest.raises(AssertionError, match="`schema` attribute must be set."):
        types.new_class(
            "TestingRepository",
            bases=(AlchemyRepository,),
            exec_body=lambda ns: ns.update(namespace),
        )


def test_subclass_alchemy_repository_wrong_schema():
    """The `schema` attribute must be of the correct type."""
    namespace = {"model": Client, "schema": str}

    with pytest.raises(TypeError, match="`schema` attribute must be a Pydantic model."):
        types.new_class(
            "TestingRepository",
            bases=(AlchemyRepository,),
            exec_body=lambda ns: ns.update(namespace),
        )
