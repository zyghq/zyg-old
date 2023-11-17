from typing import Annotated

from fastapi import Depends

from src.auth import AuthAccount, StytchAuth
from src.config import engine
from src.db.repository import AccountRepository
from src.models.account import Account


async def auth_principal(
    principal: Annotated[AuthAccount, Depends(StytchAuth())]
) -> AuthAccount:
    # (xxx) sanchitrk: can add some kind of metrics here to track
    return principal


async def active_auth_account(
    principal: Annotated[AuthAccount, Depends(auth_principal)]
) -> Account:
    # (xxx) sanchitrk: currently not doing much, but in future
    # we can check if account is active or not and raise 403 if not.

    async with engine.begin() as connection:
        repo = AccountRepository(connection=connection)
        account = await repo.get_by_auth_user_id(principal.user_id)
        return account
