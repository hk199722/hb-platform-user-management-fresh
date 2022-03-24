import binascii
import os
from typing import List

from psycopg2.errors import (  # pylint: disable=no-name-in-module
    ForeignKeyViolation,
    UniqueViolation,
)
from pydantic import UUID4
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from user_management.core.dependencies import User
from user_management.core.exceptions import RequestError
from user_management.core.security import pwd_context
from user_management.models import Client, ClientAPIToken, ClientUser, GCPUser
from user_management.repositories.base import AlchemyRepository, Order, Schema
from user_management.schemas import ClientAPITokenSchema, ClientSchema


class ClientRepository(AlchemyRepository):
    model = Client
    schema = ClientSchema

    def list_restricted(self, user: User, order_by: Order = None, **filters) -> List[Schema]:
        """Lists `Clients`s filtering the results to only those that the current user has been
        assigned to.
        """
        query = select(self.model).join(ClientUser).filter_by(gcp_user_uid=user.uid)
        results = (
            self.db.execute(
                super()._filter_and_order(query=query, order=order_by, **filters).distinct()
            )
            .scalars()
            .all()
        )
        return [self._response(entity) for entity in results]

    def delete_client_only_users(self, uid: UUID4) -> List[UUID4]:
        """Deletes `GCPUser`s that are only members of the `Client` specified by `uid`."""
        client_only_users = (
            self.db.execute(
                select(GCPUser.uid)
                .join(ClientUser)
                .where(
                    GCPUser.uid.in_(select(ClientUser.gcp_user_uid).filter_by(client_uid=uid)),
                    GCPUser.staff == False,
                )
                .group_by(GCPUser.uid)
                .having(func.count() < 2)
            )
            .scalars()
            .all()
        )
        self.db.execute(delete(GCPUser).where(GCPUser.uid.in_(client_only_users)))
        self.db.commit()

        return client_only_users

    def generate_api_token(self, uid: UUID4) -> ClientAPITokenSchema:
        """Generates an API access token, composed of a random 40-chars length string. The string is
        then encrypted to be stored in the DB, being returned as plain text to the user so it can be
        used securely on its end.
        """
        token = binascii.hexlify(os.urandom(20)).decode()
        encrypted_token = pwd_context.hash(token)

        client_api_token = ClientAPIToken(client_uid=uid, token=encrypted_token)
        self.db.add(client_api_token)

        try:
            self.db.commit()
        except IntegrityError as error:
            if isinstance(error.__cause__, ForeignKeyViolation):
                raise RequestError(context={"message": "Invalid Client UUID."}) from error
            if isinstance(error.__cause__, UniqueViolation):
                # The Client already had an API token, so this request will delete the existing and
                # re-generate a new one.
                self.db.rollback()
                existing_token = self.db.get(ClientAPIToken, uid)
                self.db.delete(existing_token)
                self.db.commit()
                return self.generate_api_token(uid=uid)

            raise error from None

        return ClientAPITokenSchema(client_uid=uid, token=token)
