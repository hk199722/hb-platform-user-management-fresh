from fastapi import APIRouter

from user_management.schemas import LoginSchema, RefreshTokenSchema
from user_management.services import GCPIdentityPlatformService


router = APIRouter()


@router.post("")
async def login(login_credentials: LoginSchema):
    login_response = await GCPIdentityPlatformService().login_gcp_user(
        email=login_credentials.email, password=login_credentials.password.get_secret_value()
    )
    return login_response


@router.post("/refresh-token")
async def refresh_token(payload: RefreshTokenSchema):
    refresh_response = await GCPIdentityPlatformService().refresh_token_gcp_user(
        refresh_token=payload.refresh_token
    )
    return refresh_response
