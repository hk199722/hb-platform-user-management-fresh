from typing import List

from sqlalchemy import select

from user_management.core.dependencies import User
from user_management.models import Client, ClientUser
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
