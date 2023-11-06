import os
from datetime import datetime

import stytch
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from stytch.consumer.models.sessions import AuthenticateResponse
from stytch.core.response_base import StytchError

stytch_client = stytch.Client(
    project_id=os.getenv("STYTCH_PROJECT_ID"),
    secret=os.getenv("STYTCH_SECRET"),
    environment=os.getenv("STYTCH_PROJECT_ENV"),
)


class AuthAccount(BaseModel):
    user_id: str
    status: str
    name: str | None = None
    created_at: datetime | None = None


class StytchAuth(HTTPBearer):
    def __init__(self, auto_error: bool = True, token_type: str = "session"):
        super().__init__(auto_error=auto_error)
        self.token_type = token_type

    async def __call__(self, request: Request) -> AuthAccount:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "Invalid authentication credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        response = await self.authenticate(credentials.credentials)
        user = response.user
        return AuthAccount(
            user_id=user.user_id,
            status=user.status,
            name=f"{user.name.first_name} {user.name.last_name}",
            created_at=user.created_at,
        )

    async def authenticate(self, token: str) -> AuthenticateResponse:
        try:
            if self.token_type == "session":
                response = await stytch_client.sessions.authenticate_async(
                    session_token=token
                )
            else:
                response = await stytch_client.sessions.authenticate_async(
                    session_jwt=token
                )
            return response
        except StytchError as error:
            if error.details.status_code >= 400:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "message": "Invalid authentication credentials or session expired"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                ) from error
            if error.details.status_code == 503:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={"message": "Service unavailable"},
                ) from error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": "Internal server error"},
            ) from error
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": "Internal server error"},
            ) from error
