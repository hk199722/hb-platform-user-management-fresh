from psycopg2.errors import (  # pylint: disable=no-name-in-module
    ForeignKeyViolation,
    UniqueViolation,
)
from sqlalchemy.exc import IntegrityError

from user_management.core.exceptions import RequestError, ResourceConflictError
from user_management.models import Capability, ClientCapability
from user_management.repositories.base import AlchemyRepository
from user_management.schemas import CapabilitySchema, ClientCapabilitySchema


class CapabilityRepository(AlchemyRepository):
    model = Capability
    schema = CapabilitySchema

    def assign_client_capability(self, client_capability: ClientCapabilitySchema) -> None:
        """
        Given a Client UUID and a Capability ID it creates a new `ClientCapability` row, effectively
        enabling that capability for the client.
        """
        new_client_capability = ClientCapability(**client_capability.dict())
        self.db.add(new_client_capability)

        try:
            self.db.commit()
        except IntegrityError as error:
            if isinstance(error.__cause__, ForeignKeyViolation):
                raise RequestError(
                    context={"message": "Invalid Capability ID or Client UUID."}
                ) from error
            if isinstance(error.__cause__, UniqueViolation):
                raise ResourceConflictError(
                    context={"message": "Selected Capability is already enabled for client."}
                ) from error

            raise error from None
