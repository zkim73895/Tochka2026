import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.flows.catalog import lookup_market_asset
from exchange_kernel.flows.identity import resolve_profile
from exchange_kernel.storage.gateway import provide_session
from exchange_kernel.storage.schema import MarketAsset, TraderProfile


async def load_asset(
    ticker: str,
    session: AsyncSession = Depends(provide_session),
) -> MarketAsset:
    asset = await lookup_market_asset(session, ticker)
    if not asset:
        raise HTTPException(404)
    return asset


async def load_profile(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(provide_session),
) -> TraderProfile:
    profile = await resolve_profile(session, str(user_id))
    if not profile:
        raise HTTPException(404)
    return profile

