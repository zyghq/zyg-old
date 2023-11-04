import logging

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.db.repository import AccountRepository
from src.models.account import Account

logger = logging.getLogger(__name__)


router = APIRouter()


class GetOrCreateAuthAccountRequest(BaseModel):
    provider: str
    auth_user_id: str
    name: str


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
