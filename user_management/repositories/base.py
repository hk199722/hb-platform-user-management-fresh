import re
from datetime import datetime, timezone
from typing import Any, Generic, List, NamedTuple, Type, TypeVar

from psycopg2.errors import (  # pylint: disable=no-name-in-module
    ForeignKeyViolation,
    UniqueViolation,
)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, Query
from sqlalchemy.sql.selectable import Select

from user_management.core.database import Base
from user_management.core.exceptions import ResourceConflictError, ResourceNotFoundError


# Type to return Pydantic model instances from the repository.
Schema = TypeVar("Schema", bound="BaseModel")

PATTERN = re.compile(r'.*Key (.*) is not present in table "(.*)".', flags=re.DOTALL)


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
        if bases and name != "AlchemyRepository":
            model = class_dict.get("model")
            assert model is not None, "`model` attribute must be set."
            if not issubclass(model, Base):
                raise TypeError("`model` attribute must be a SQLAlchemy model.")

            schema = class_dict.get("schema")
            assert schema is not None, "`schema` attribute must be set."
            if not issubclass(schema, BaseModel):
                raise TypeError("`schema` attribute must be a Pydantic model.")

        return type.__new__(mcs, name, bases, class_dict)


class AlchemyRepository(Generic[Schema], metaclass=MetaAlchemyRepository):
    """
    Repository class to be used with SQLAlchemy ORM models. Implements convenience basic CRUD
    methods for DB access. Can be extended with more specific methods if needed.
    """

    model: Type[Base]
    schema: Type[Schema]

    def __init__(self, db: Session):
        self.db = db

        # Get data model properties from Pydantic schema.
        self.properties = self.schema.schema().get("properties", {})
        assert bool(self.properties), "`schema` must not be empty."

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
                match = PATTERN.search(str(e.__cause__))
                if match is not None:
                    values, table = match.groups()
                    raise ResourceNotFoundError(
                        {"message": f"{table.title()} does not exist with values {values}"}
                    ) from ForeignKeyViolation

            raise e from None

    def _filter_and_order(self, query: Select, order: Order = None, **kwargs) -> Query:
        if kwargs:
            query = query.filter_by(**kwargs)
        if order:
            query = query.order_by(getattr(getattr(self.model, order.column), order.direction)())

        return query

    def _select_from_db(self, pk: Any) -> Base:
        if entity := self.db.get(self.model, pk):
            return entity

        raise ResourceNotFoundError({"message": f"No {self.model_name} found with id {pk}"})

    def _response(self, entity: Base) -> Schema:
        values = {key: getattr(entity, key) for key in self.properties.keys()}
        return self.schema(**values)

    def create(self, schema: BaseModel) -> Schema:
        values = schema.dict().items()
        row = {key: value for key, value in values if key in self.model.__table__.columns.keys()}
        entity = self.model(**row)
        self.db.add(entity)
        self._persist_changes(schema=schema)
        self.db.refresh(entity)

        return self._response(entity)

    def get(self, pk: Any) -> Schema:
        """Returns a single object from a DB table, given its primary key value."""
        entity = self._select_from_db(pk=pk)
        return self._response(entity)

    def list(self, order_by: Order = None, **filters) -> List[Schema]:
        """Lists all the objects for the given filter and order"""
        query = select(self.model)

        results = (
            self.db.execute(self._filter_and_order(query=query, order=order_by, **filters))
            .scalars()
            .all()
        )
        return [self._response(entity) for entity in results]

    def update(self, pk: Any, schema: BaseModel) -> Schema:
        """Updates a single object from a DB table, given its primary key value."""
        entity = self._select_from_db(pk=pk)
        for key, val in schema.dict(exclude_unset=True).items():
            setattr(entity, key, val)
        if hasattr(entity, "updated_at"):
            setattr(entity, "updated_at", datetime.now(timezone.utc))

        self._persist_changes(schema=schema)

        return self._response(entity)

    def delete(self, pk: Any) -> None:
        """Deletes a single object from a DB table, given its primary key value."""
        entity = self._select_from_db(pk=pk)
        self.db.delete(entity)
        self.db.commit()
