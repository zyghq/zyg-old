import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.config import engine
from src.auth import AuthAccount
from src.db.repository import AccountRepository
from src.models.account import Account
from src.web.deps import active_auth_account, auth_principal

logger = logging.getLogger(__name__)


router = APIRouter()


class AccountEmail(BaseModel):
    email: str
    verified: bool


class GetOrCreateAuthAccountRequest(BaseModel):
    provider: str
    name: str
    emails: List[AccountEmail]


@router.post("/auth/")
async def get_or_create_auth_account(
    body: GetOrCreateAuthAccountRequest,
    principal: Annotated[AuthAccount, Depends(auth_principal)],
):
    logger.info("get or create auth account...")

    def get_first_verified_email() -> str | None:
        """
        In Stytch we can have multiple verified emails, but we only want to use the
        first one. Also we assume that this implementation of Stytch is also in our control.

        Let's not link multiple emails to a single account for now. Keep it simple.
        Also, we don't want to change the email of an account once created, so we'll just use the
        first verified email. This also makes our email as natural primary key.
        """
        for email in body.emails:
            if email.verified:
                return email.email
        return None

    email = get_first_verified_email()

    if not email:
        return JSONResponse(
            status_code=400,
            content={"error": "No verified email found for auth account."},
        )

    auth_user_id = principal.user_id

    async with engine.begin() as connection:
        repo = AccountRepository(connection=connection)
        account = await repo.find_by_auth_user_id(auth_user_id)
        if account:
            return JSONResponse(
                status_code=200,
                content=jsonable_encoder(account.to_dict()),
            )

        account = Account(
            account_id=None,
            provider=body.provider,
            auth_user_id=auth_user_id,
            email=email,
            name=body.name,
            created_at=None,
            updated_at=None,
        )
        account = await repo.save(account)
        return JSONResponse(
            status_code=201,
            content=jsonable_encoder(account.to_dict()),
        )


@router.get("/auth/")
async def auth_account(account: Annotated[Account, Depends(active_auth_account)]):
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(account.to_dict()),
    )
