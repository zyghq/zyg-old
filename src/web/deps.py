from typing import Annotated

from fastapi import Depends

from src.auth import AuthAccount, StytchAuth
from src.db.repository import AccountRepository
from src.models.account import Account


async def auth_account(
    principal: Annotated[AuthAccount, Depends(StytchAuth())]
) -> Account:
    repo = AccountRepository()
    account = await repo.get_by_auth_user_id(principal.user_id)
    return account


async def active_auth_account(
    account: Annotated[Account, Depends(auth_account)]
) -> Account:
    # (xxx) sk: currently to checking for status, but we can do that here.
    # can raise 403 if account is not active
    return account
