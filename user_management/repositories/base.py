import re
from datetime import datetime, timezone
from typing import Any, List, NamedTuple, Type

from psycopg2.errors import (  # pylint: disable=no-name-in-module
    ForeignKeyViolation,
    UniqueViolation,
)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, Query

from user_management.core.database import Base
from user_management.core.exceptions import ResourceConflictError, ResourceNotFoundError


pattern = re.compile(r'.*Key (.*) is not present in table "(.*)".', flags=re.DOTALL)


class Order(NamedTuple):
    direction: str
    column: str

    @classmethod
    def asc(cls, column: str) -> "Order":
        return cls(direction="asc", column=column)

    @classmethod
    def desc(cls, column: str) -> "Order":
        return cls(direction="desc", column=column)


class MetaAlchemyRepository(type):
    """
    Metaclass for `AlchemyRepository` to enforce all subclasses to follow defined patterns for
    attributes.
    """

    def __new__(mcs, name, bases, class_dict):
        if bases:
            model = class_dict.get("model")
            assert model is not None, "`model` attribute must be set."
            if not issubclass(model, Base):
                raise TypeError("`model` attribute must be a SQLAlchemy model.")

            schema = class_dict.get("schema")
            assert schema is not None, "`schema` attribute must be set."
            if not issubclass(schema, BaseModel):
                raise TypeError("`schema` attribute must be a Pydantic model.")

        return type.__new__(mcs, name, bases, class_dict)


class AlchemyRepository(metaclass=MetaAlchemyRepository):
    """
    Repository class to be used with SQLAlchemy ORM models. Implements convenience basic CRUD
    methods for DB access. Can be extended with more specific methods if needed.
    """

    model: Type[Base]
    schema: Type[BaseModel]

    def __init__(self, db: Session):
        self.db = db

    @property
    def model_name(self):
        return type(self.model()).__name__.lower()

    def _persist_changes(self, schema: BaseModel):
        """Helper method that attempts to persist changes into the database.

        It handles the actual database integrity errors via the Psycopg2 connector exceptions, and
        returns appropriate custom application exceptions that can be handled upstream by functions
        or classes that uses `AlchemyRepository` based repositories.
        """
        try:
            self.db.commit()
        except IntegrityError as e:
            if isinstance(e.__cause__, UniqueViolation):
                raise ResourceConflictError(
                    {"message": f"{self.model_name} already exists with {schema}"}
                ) from UniqueViolation
            if isinstance(e.__cause__, ForeignKeyViolation):
                # SQLAlchemy exceptions give too much detail about the infrastructure
                match = pattern.search(str(e.__cause__))
                if match is not None:
                    values, table = match.groups()
                    raise ResourceNotFoundError(
                        {"message": f"{table.title()} does not exist with values {values}"}
                    ) from ForeignKeyViolation

            raise e from None

    def create(self, schema: BaseModel) -> Base:
        record = self.model(**schema.dict())
        self.db.add(record)
        self._persist_changes(schema=schema)
        self.db.refresh(record)

        return record

    def _filter_and_order(self, order: Order = None, **kwargs) -> Query:
        query = select(self.model)

        if kwargs:
            query = query.filter_by(**kwargs)

        if order:
            query = query.order_by(getattr(getattr(self.model, order.column), order.direction)())

        return query

    def get(self, _id: Any) -> Base:
        """Returns a single object from a DB table, given its primary key value."""
        if entity := self.db.get(self.model, _id):
            return entity

        raise ResourceNotFoundError({"message": f"No {self.model_name} found with id {_id}"})

    def list(self, order_by: Order = None, **filters) -> List[Base]:
        """Lists all the objects for the given filter and order"""
        return self.db.execute(self._filter_and_order(order=order_by, **filters)).scalars().all()

    def update(self, _id: Any, schema: BaseModel) -> Base:
        entity = self.get(_id)
        for key, val in schema.dict().items():
            setattr(entity, key, val)
        if hasattr(entity, "updated_at"):
            setattr(entity, "updated_at", datetime.now(timezone.utc))

        self._persist_changes(schema=schema)

        return entity

    def delete(self, _id: Any) -> None:
        """Deletes a single object from a DB table, given its primary key value."""
        entity = self.get(_id=_id)
        self.db.delete(entity)
        self.db.commit()
