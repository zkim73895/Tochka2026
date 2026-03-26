from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.access.profiles import fetch_profile, spawn_profile, store_api_key
from exchange_kernel.foundation.config import load_config
from exchange_kernel.storage.schema import ProfileKind, TraderProfile


def mint_access_key(claims: dict, expires_delta: timedelta | None = None) -> str:
    config = load_config()
    payload = claims.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta is not None else timedelta(minutes=config.token_ttl_minutes)
    )
    payload.update({"exp": expire})
    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)


async def onboard_profile(session: AsyncSession, display_name: str) -> tuple[TraderProfile, str]:
    profile = await spawn_profile(session, display_name)
    claims = {"name": profile.name, "id": str(profile.id), "role": profile.role.name}
    api_key = mint_access_key(claims)
    profile = await store_api_key(session, profile, api_key)
    return profile, api_key


async def resolve_profile(session: AsyncSession, profile_id: str) -> TraderProfile | None:
    return await fetch_profile(session, profile_id)


async def require_admin(profile: TraderProfile) -> TraderProfile:
    if profile.role != ProfileKind.ADMIN:
        raise HTTPException(status_code=403, detail="Permission denied", headers={"WWW-Authenticate": "TOKEN"})
    return profile

