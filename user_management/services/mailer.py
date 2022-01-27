import json
import logging
from typing import Any, Dict

from google.cloud.pubsub_v1 import PublisherClient
from google.cloud.pubsub_v1.types import LimitExceededBehavior, PublisherOptions, PublishFlowControl
from pydantic import UUID4

from user_management.core.config.settings import get_settings
from user_management.core.dependencies import DBSession
from user_management.repositories.gcp_user import GCPUserRepository
from user_management.services.gcp_identity import GCPIdentityPlatformService


logger = logging.getLogger(__name__)


class MailerService:
    """Service to send email notifications to users."""

    def __init__(self, db: DBSession):
        settings = get_settings()

        self.gcp_user_repository = GCPUserRepository(db)
        self.gcp_identity_service = GCPIdentityPlatformService()
        self.client = PublisherClient(
            publisher_options=PublisherOptions(
                flow_control=PublishFlowControl(
                    message_limit=settings.message_limit,
                    byte_limit=settings.byte_limit,
                    # Fail hard if so many messages are stacking in the Pub/Sub queue.
                    limit_exceeded_behavior=LimitExceededBehavior.ERROR,
                )
            )
        )
        self.topic_path = self.client.topic_path(  # pylint: disable=no-member
            project=settings.gcp_project, topic=settings.topic_name
        )

    @staticmethod
    def encode_message(message: Dict[str, Any]) -> bytes:
        """Helper function to encode the message to be published in GCP Pub/Sub as needed."""
        return json.dumps(message).encode("utf-8")

    def reset_password_message(self, gcp_user_uid: UUID4) -> None:
        gcp_user = self.gcp_user_repository.get(pk=gcp_user_uid)
        message = {
            "message_type": "PASSWORD_RESET",
            "email": gcp_user.email,
            "context": {
                "full_name": gcp_user.name,
                "reset_password_link": self.gcp_identity_service.get_password_reset_link(gcp_user),
            },
        }
        published = self.client.publish(self.topic_path, self.encode_message(message))
        response = published.result()

        logger.info(
            "Reset password email sent to user %s (%s). Message ID: %s.",
            gcp_user.email,
            gcp_user_uid,
            response,
        )
