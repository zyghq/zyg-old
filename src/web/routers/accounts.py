import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from src.auth import AuthAccount, StytchAuth
from src.db.repository import AccountRepository
from src.models.account import Account

logger = logging.getLogger(__name__)


router = APIRouter()


class GetOrCreateAuthAccountRequest(BaseModel):
    provider: str
    auth_user_id: str
    name: str


http_bearer_schema = HTTPBearer()


async def get_auth_account(
    principal: Annotated[AuthAccount, Depends(StytchAuth())]
) -> Account:
    print("******* principal ********")
    print(principal)
    auth_user_id = "123456789"
    repo = AccountRepository()
    account = await repo.get_by_auth_user_id(auth_user_id)
    return account


async def get_active_account(
    account: Annotated[Account, Depends(get_auth_account)]
) -> Account:
    return account


@router.post("/auth/")
async def get_or_create_auth_account(body: GetOrCreateAuthAccountRequest):
    logger.info("get_or_create_auth_account")
    repo = AccountRepository()
    account = await repo.find_by_auth_user_id(body.auth_user_id)
    if account is None:
        account = Account(
            account_id=None,
            provider=body.provider,
            auth_user_id=body.auth_user_id,
            name=body.name,
            created_at=None,
            updated_at=None,
        )
        account = await repo.save(account)
        return JSONResponse(
            status_code=201,
            content=jsonable_encoder(account.to_dict()),
        )
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(account.to_dict()),
    )


@router.get("/auth/")
async def get_auth_account(account: Annotated[Account, Depends(get_active_account)]):
    print("******** got account in get_auth_account ********")
    print(account)
    return "get_auth_account"
