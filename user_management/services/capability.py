from typing import List, Optional

from user_management.core.dependencies import DBSession
from user_management.repositories import CapabilityRepository
from user_management.repositories.base import Order
from user_management.schemas import CapabilitySchema, ClientCapabilitySchema, NewNamedEntitySchema


class CapabilityService:
    def __init__(self, db: DBSession):
        self.capability_repository = CapabilityRepository(db)

    def create_capability(self, capability: NewNamedEntitySchema) -> CapabilitySchema:
        return self.capability_repository.create(schema=capability)

    def get_capability(self, capability_id: int) -> CapabilitySchema:
        return self.capability_repository.get(pk=capability_id)

    def list_capabilities(
        self, order_by: Optional[Order] = Order.asc("name")
    ) -> List[CapabilitySchema]:
        return self.capability_repository.list(order_by=order_by)

    def enable_capability(self, client_capability: ClientCapabilitySchema) -> None:
        return self.capability_repository.assign_client_capability(
            client_capability=client_capability
        )
