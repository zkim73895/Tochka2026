from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.access.assets import erase_asset, fetch_asset, fetch_assets, register_asset


async def list_market_assets(session: AsyncSession):
    return await fetch_assets(session)


async def lookup_market_asset(session: AsyncSession, ticker: str):
    return await fetch_asset(session, ticker)


async def create_market_asset(session: AsyncSession, name: str, ticker: str):
    existing = await fetch_asset(session, ticker)
    if existing:
        raise HTTPException(422)
    return await register_asset(session, name, ticker)


async def remove_market_asset(session: AsyncSession, asset):
    return await erase_asset(session, asset)

