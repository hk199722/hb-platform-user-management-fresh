from typing import List

from pydantic import UUID4
from sqlalchemy import delete, func, select

from user_management.core.dependencies import User
from user_management.models import Client, ClientUser, GCPUser
from user_management.repositories.base import AlchemyRepository, Order, Schema
from user_management.schemas import ClientSchema


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
