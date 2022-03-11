from user_management.core.dependencies import DBSession
from user_management.repositories import CapabilityRepository
from user_management.schemas import CapabilitySchema, NewNamedEntitySchema


class CapabilityService:
    def __init__(self, db: DBSession):
        self.capability_repository = CapabilityRepository(db)

    def create_capability(self, capability: NewNamedEntitySchema) -> CapabilitySchema:
        return self.capability_repository.create(schema=capability)
