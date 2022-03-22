import logging
from typing import Dict, List, TypedDict, Union

from fastapi import status
from firebase_admin.auth import (
    create_user,
    delete_user,
    delete_users,
    EmailAlreadyExistsError,
    generate_password_reset_link,
    PhoneNumberAlreadyExistsError,
    set_custom_user_claims,
    UidAlreadyExistsError,
    update_user,
    UserNotFoundError,
)
from firebase_admin.exceptions import FirebaseError, InvalidArgumentError, PermissionDeniedError
from pydantic import EmailStr, UUID4
from requests import Session

from user_management.core.config.settings import get_settings
from user_management.core.exceptions import (
    AuthenticationError,
    RemoteServiceError,
    RequestError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from user_management.core.firebase import init_identity_platform_app
from user_management.schemas import GCPUserSchema


logger = logging.getLogger(__name__)

Claims = TypedDict("Claims", {"roles": Dict[str, str], "staff": bool}, total=False)


class GCPIdentityPlatformService:
    """Service implementation to communicate and synchronize data with GCP Identity Platform."""

    def __init__(self):
        self.api_key = get_settings().gcp_api_key.get_secret_value()
        self.api_session = Session()

    @staticmethod
    def _handle_gcp_exception(error: Exception, gcp_user: Union[GCPUserSchema, UUID4]) -> None:
        """Helper method to handle all possible error responses from GCP in detail."""
        logger.error("Error syncing users data with GCP Identity Platform: %s", str(error))

        map_exceptions = {
            EmailAlreadyExistsError: (ResourceConflictError, "Duplicated email."),
            InvalidArgumentError: (RequestError, str(error)),
            PhoneNumberAlreadyExistsError: (ResourceConflictError, "Duplicated phone number."),
            UidAlreadyExistsError: (ResourceConflictError, "Duplicated UID."),
            UserNotFoundError: (ResourceNotFoundError, "User not found."),
            PermissionDeniedError: (RemoteServiceError, str(error)),
            FirebaseError: (RemoteServiceError, str(error)),
            ValueError: (RequestError, str(error)),
            # Handle any unexpected exception form GCP-IP.
            Exception: (RemoteServiceError, str(error)),
        }

        exception_class, message = map_exceptions[type(error)]
        context: dict = {"message": message}

        # Build exception response context with the available data.
        if isinstance(gcp_user, GCPUserSchema):
            context.update(
                {
                    "message": message,
                    "uid": str(gcp_user.uid),
                    "email": gcp_user.email,
                    "phone_number": gcp_user.phone_number,
                }
            )
        else:
            context.update({"uid": str(gcp_user)})

        raise exception_class(context=context) from error

    def sync_gcp_user(self, gcp_user: GCPUserSchema, update: bool = False) -> None:
        """Synchronizes data from a local DB `GCPUser` with GCP."""
        if not init_identity_platform_app():
            logger.debug("GCP Identity Platform not connected. New user not synced.")
            return

        try:
            if update is False:
                create_user(uid=str(gcp_user.uid), display_name=gcp_user.name, email=gcp_user.email)
            else:
                update_user(uid=str(gcp_user.uid), display_name=gcp_user.name, email=gcp_user.email)
        except Exception as error:  # pylint: disable=broad-except
            self._handle_gcp_exception(error, gcp_user)

        # Synchronize user claims.
        claims: Claims = {
            "staff": gcp_user.staff,
            "roles": {
                str(client_user.client_uid): client_user.role.value
                for client_user in gcp_user.clients
            },
        }
        try:
            set_custom_user_claims(str(gcp_user.uid), claims)
        except Exception as error:  # pylint: disable=broad-except
            self._handle_gcp_exception(error, gcp_user)

    def remove_gcp_user(self, uid: UUID4) -> None:
        """Removes a user from GCP Identity Platform remote backend, given its GCP-IP user ID."""
        try:
            delete_user(uid=str(uid))
        except Exception as error:  # pylint: disable=broad-except
            self._handle_gcp_exception(error, uid)

    @staticmethod
    def remove_bulk_gcp_users(uids: List[UUID4]) -> None:
        """Given a list of user IDs, removes them in bulk from GCP-IP backend."""
        chunk: list = []

        def remove_users(gcp_users: list) -> None:
            try:
                delete_users(uids=gcp_users)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Error when trying to delete users in GCP-IP.")

        # GCP-IP/Firebase SDK allows a maximum of 1000 user UUIDs to be submitted for deletion at
        # once. We are likely not reaching that limit, but is just safer to behave like if we will.
        for count, uid in enumerate(uids, 1):
            chunk.append(str(uid))
            if count % 1000 == 0:
                remove_users(gcp_users=chunk)
                chunk.clear()

        if chunk:
            remove_users(gcp_users=chunk)

    @staticmethod
    def get_password_reset_link(gcp_user: GCPUserSchema) -> str:
        """Generates and returns the "reset password" link for the given GCP-IP user email."""
        return generate_password_reset_link(email=gcp_user.email)

    def set_password(self, gcp_user_uid: UUID4, password: str):
        """Sets up the user password for the given GCP-IP user ID."""
        try:
            update_user(uid=gcp_user_uid, password=password)
        except Exception as error:  # pylint: disable=broad-except
            self._handle_gcp_exception(error, gcp_user_uid)

        logger.info("User %s password has been successfully set up.", gcp_user_uid)

    async def login_gcp_user(self, email: EmailStr, password: str):
        """
        Performs a request to GCP Identity Platform REST API to sign in a user using its email and
        password.

        When submitting login info to GCP-IP, we handle 3 types of situations:
        - Successful authentication by the user (should be the most common case).
        - Invalid credentials submitted by the user, login denied. GCP-IP returns a `400` error for
          this, rather than a 401 error (which should be the correct thing).
        - Invalid GCP API key, which is a User Management Service misconfiguration. This is returned
          as a `500` error with the app exception `RemoteServiceError` and an informative message.
          This should never happen, but if it does and the users are seeing this when trying to log
          in, the problem is immediately identified.

        Other possible errors are mostly undocumented in GCP.
        """
        response = self.api_session.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}",
            data={"email": email, "password": password, "returnSecureToken": True},
        )

        if response.status_code == status.HTTP_400_BAD_REQUEST:
            message = response.json()
            if message.get("error", {}).get("status") == "INVALID_ARGUMENT":
                raise RemoteServiceError(context={"message": "Service unavailable."})

            raise AuthenticationError(context={"message": "Invalid credentials."})

        return response.json()
