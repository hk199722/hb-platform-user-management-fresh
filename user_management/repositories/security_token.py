from pydantic import UUID4

from sqlalchemy import select

from user_management.models import SecurityToken
from user_management.repositories.base import AlchemyRepository
from user_management.schemas import SecurityTokenSchema


class SecurityTokenRepository(AlchemyRepository):
    model = SecurityToken
    schema = SecurityTokenSchema

    def get_user_token(self, gcp_user_uid: UUID4) -> SecurityTokenSchema:
        token = (
            self.db.execute(select(self.model).filter_by(gcp_user_uid=gcp_user_uid)).scalars().one()
        )

        return self._response(token)
