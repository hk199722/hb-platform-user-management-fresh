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
    RequestError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from user_management.core.firebase import init_identity_provider_app
from user_management.schemas import GCPUserSchema


logger = logging.getLogger(__name__)


class GCPIdentityProviderService:
    def sync_gcp_user(self, gcp_user: GCPUserSchema, update: bool = False) -> None:
        if not init_identity_provider_app():
            logger.debug("GCP Identity Provider not connected. New user not synced.")
            return

        try:
            if update is False:
                create_user(uid=str(gcp_user.uid), display_name=gcp_user.name, email=gcp_user.email)
            else:
                update_user(uid=str(gcp_user.uid), display_name=gcp_user.name, email=gcp_user.email)
        except EmailAlreadyExistsError as error:
            logger.error(
                "Unable to create user in GCP Identity Platform. Duplicated email: %s",
                gcp_user.email,
            )
            raise ResourceConflictError(
                context={
                    "message": "Duplicated email.",
                    "uid": str(gcp_user.uid),
                    "email": gcp_user.email,
                    "phone_number": gcp_user.phone_number,
                }
            ) from error
        except UidAlreadyExistsError as error:
            logger.error(
                "Unable to create user in GCP Identity Platform. Duplicated UID: %s", gcp_user.uid
            )
            raise ResourceConflictError(
                context={
                    "message": "Duplicated UID.",
                    "uid": str(gcp_user.uid),
                    "email": gcp_user.email,
                    "phone_number": gcp_user.phone_number,
                }
            ) from error
        except PhoneNumberAlreadyExistsError as error:
            logger.error(
                "Unable to create user in GCP Identity Platform. Duplicated phone number: %s",
                gcp_user.phone_number,
            )
            raise ResourceConflictError(
                context={
                    "message": "Duplicated phone number.",
                    "uid": str(gcp_user.uid),
                    "email": gcp_user.email,
                    "phone_number": gcp_user.phone_number,
                }
            ) from error
        except UserNotFoundError as error:
            logger.error(
                "Unable to modify user in GCP Identity Platform. User not found: %s",
                gcp_user.uid,
            )
            raise ResourceNotFoundError(
                context={
                    "message": "User not found.",
                    "uid": str(gcp_user.uid),
                    "email": gcp_user.email,
                    "phone_number": gcp_user.phone_number,
                }
            ) from error
        except (InvalidArgumentError, ValueError) as error:
            logger.error("Invalid request to GCP Identity Platform: %s", str(error))
            raise RequestError(
                context={
                    "message": str(error),
                    "uid": str(gcp_user.uid),
                    "email": gcp_user.email,
                    "phone_number": gcp_user.phone_number,
                }
            ) from error
