from user_management.models import Capability
from user_management.repositories.base import AlchemyRepository
from user_management.schemas import CapabilitySchema


class CapabilityRepository(AlchemyRepository):
    model = Capability
    schema = CapabilitySchema
