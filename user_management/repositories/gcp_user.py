from typing import Iterable, List, Optional

from pydantic import BaseModel, EmailStr, UUID4
from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound

from user_management.core.exceptions import ResourceNotFoundError
from user_management.models import ClientUser, GCPUser, Role
from user_management.repositories.base import AlchemyRepository, Order, Schema
from user_management.schemas import ClientUserSchema, GCPUserSchema


class GCPUserRepository(AlchemyRepository):
    model = GCPUser
    schema = GCPUserSchema

    def _persist_user_role(self, schema: BaseModel, ready_response: GCPUserSchema):
        """Helper method to check up for submitted user roles for a given client."""
        client_user: Optional[ClientUserSchema] = getattr(schema, "role", None)
        if client_user is not None:
            # User role passed in.
            existing_client_user = self.db.get(
                ClientUser,
                {"client_uid": client_user.client_uid, "gcp_user_uid": ready_response.uid},
            )

            if existing_client_user:
                # User already has a role in the given Client.
                if existing_client_user.role == client_user.role:
                    # The user already has this role in the given Client. So don't do anything.
                    return ready_response

                # Role has changed.
                existing_client_user.role = client_user.role
                ready_response.clients = [existing_client_user]
            else:
                # Create new role for given Client.
                new_client_user = ClientUser(
                    client_uid=client_user.client_uid,
                    gcp_user_uid=ready_response.uid,
                    role=client_user.role,
                )
                self.db.add(new_client_user)
                ready_response.clients = [new_client_user]

        self._persist_changes(schema=schema)
        return ready_response

    def get_from_email(self, email: EmailStr) -> GCPUserSchema:
        try:
            gcp_user = self.db.execute(select(self.model).filter_by(email=email)).scalars().one()
        except NoResultFound as error:
            raise ResourceNotFoundError(
                context={"message": f"No user found for email {email}."}
            ) from error

        return self._response(gcp_user)

    def create(self, schema: BaseModel) -> Schema:
        """Overrides base `create` method to handle user roles creation for a given client"""
        response = super().create(schema=schema)

        return self._persist_user_role(schema=schema, ready_response=response)

    def update(self, pk: UUID4, schema: BaseModel) -> Schema:
        """Overrides base `update` method to handle user roles modifications for a given client."""
        response = super().update(pk=pk, schema=schema)

        return self._persist_user_role(schema=schema, ready_response=response)

    def list_restricted(
        self,
        clients: List[UUID4],
        order_by: Order = None,
        **filters,
    ) -> List[Schema]:
        """Lists `GCPUser`s filtering the results to only those users that belong to the passed list
        of clients (by `Client.uid`).
        """
        query = select(self.model).join(ClientUser).filter(ClientUser.client_uid.in_(clients))
        results = (
            self.db.execute(
                super()._filter_and_order(query=query, order=order_by, **filters).distinct()
            )
            .scalars()
            .all()
        )
        return [self._response(entity) for entity in results]

    def delete_client_user(self, gcp_user: UUID4, client: UUID4) -> None:
        """Given a `GCPUser` UUID and a `Client` UUID, it finds the associative object between both
        and deletes its row in the database.
        """
        if client_user := self.db.get(ClientUser, {"gcp_user_uid": gcp_user, "client_uid": client}):
            self.db.delete(client_user)
            return self.db.commit()

        raise ResourceNotFoundError(
            {"message": f"User {gcp_user} doesn't have a role with Client {client}."}
        )

    def get_matching_clients(
        self, gcp_user_uid: UUID4, clients: Iterable[UUID4]
    ) -> List[ClientUser]:
        """Given a `GCPUser.uid` and an iterable of `Client.uid`s, it returns a list of `Client.uid`
        the user belongs to, from the given iterable.
        """
        return self.db.execute(
            select([ClientUser.client_uid, ClientUser.role])
            .filter_by(gcp_user_uid=gcp_user_uid)
            .filter(ClientUser.client_uid.in_(clients))
        ).all()

    def get_superuser_role(self, gcp_user_uid: UUID4, client_uid: UUID4) -> bool:
        """Finds if the given `gcp_user_uid` is a `Role.SUPERUSER` within `client_uid`."""
        return bool(
            self.db.execute(
                select(func.count())
                .select_from(ClientUser)
                .filter_by(gcp_user_uid=gcp_user_uid, client_uid=client_uid, role=Role.SUPERUSER)
            ).scalar()
        )
