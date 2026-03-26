from datetime import timedelta

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.foundation.config import load_config
from exchange_kernel.flows.identity import mint_access_key, require_admin, resolve_profile
from exchange_kernel.storage.gateway import provide_session
from exchange_kernel.storage.schema import TraderProfile


class TokenHeaderReader:
    def __init__(self, prefix: str = "TOKEN"):
        self.prefix = prefix

    async def __call__(self, request: Request) -> str:
        raw_header: str | None = request.headers.get("Authorization")
        if not raw_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": self.prefix},
            )
        try:
            header_prefix, token = raw_header.split(" ")
            if header_prefix != self.prefix:
                raise ValueError("Invalid token prefix")
            return token
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization format",
                headers={"WWW-Authenticate": self.prefix},
            )


read_token = TokenHeaderReader(prefix="TOKEN")


def issue_api_key(claims: dict, expires_delta: timedelta | None = None) -> str:
    return mint_access_key(claims, expires_delta)


async def require_identity(
    token: str = Depends(read_token),
    session: AsyncSession = Depends(provide_session),
) -> TraderProfile:
    config = load_config()
    auth_error = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "TOKEN"},
    )
    try:
        payload = jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])
        profile_id: str | None = payload.get("id")
        if profile_id is None:
            raise auth_error
    except jwt.PyJWTError:
        raise auth_error

    profile = await resolve_profile(session, profile_id)
    if profile:
        return profile
    raise auth_error


async def require_backoffice(profile: TraderProfile = Depends(require_identity)) -> TraderProfile:
    return await require_admin(profile)

