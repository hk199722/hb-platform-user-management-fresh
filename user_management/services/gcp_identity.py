import logging

from firebase_admin.auth import (
    create_user,
    EmailAlreadyExistsError,
    PhoneNumberAlreadyExistsError,
    UidAlreadyExistsError,
    update_user,
    UserNotFoundError,
)
from firebase_admin.exceptions import InvalidArgumentError
from user_management.core.exceptions import (
    RemoteServiceError,
    RequestError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from user_management.core.firebase import init_identity_provider_app
from user_management.schemas import GCPUserSchema


logger = logging.getLogger(__name__)


class GCPIdentityPlatformService:
    """Service implementation to communicate and synchronize data with GCP Identity Platform."""

    @staticmethod
    def _handle_gcp_exception(error: Exception, gcp_user: GCPUserSchema) -> None:
        """Helper method to handle all possible error responses from GCP in detail."""
        logger.error("Error syncing users data with GCP Identity Platform: %s", str(error))

        map_exceptions = {
            EmailAlreadyExistsError: (ResourceConflictError, "Duplicated email."),
            InvalidArgumentError: (RequestError, str(error)),
            PhoneNumberAlreadyExistsError: (ResourceConflictError, "Duplicated phone number."),
            UidAlreadyExistsError: (ResourceConflictError, "Duplicated UID."),
            UserNotFoundError: (ResourceNotFoundError, "User not found."),
            ValueError: (RequestError, str(error)),
            # Handle any unexpected exception form GCP-IP.
            Exception: (RemoteServiceError, str(error)),
        }

        exception_class, message = map_exceptions[type(error)]

        raise exception_class(
            context={
                "message": message,
                "uid": str(gcp_user.uid),
                "email": gcp_user.email,
                "phone_number": gcp_user.phone_number,
            }
        ) from error

    def sync_gcp_user(self, gcp_user: GCPUserSchema, update: bool = False) -> None:
        """Synchronizes data from a local DB `GCPUser` with GCP."""
        if not init_identity_provider_app():
            logger.debug("GCP Identity Provider not connected. New user not synced.")
            return

        try:
            if update is False:
                create_user(uid=str(gcp_user.uid), display_name=gcp_user.name, email=gcp_user.email)
            else:
                update_user(uid=str(gcp_user.uid), display_name=gcp_user.name, email=gcp_user.email)
        except Exception as error:  # pylint: disable=broad-except
            self._handle_gcp_exception(error, gcp_user)
