from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.storage.schema import AssetLedger, MarketAsset, TraderProfile


async def register_asset(session: AsyncSession, title: str, ticker: str) -> MarketAsset:
    asset = MarketAsset(name=title, ticker=ticker)
    session.add(asset)
    profiles = (await session.execute(select(TraderProfile))).scalars().all()
    for profile in profiles:
        session.add(AssetLedger(owner=profile, asset=asset, quantity=0.0))
    await session.commit()
    await session.refresh(asset)
    return asset


async def fetch_asset(session: AsyncSession, ticker: str) -> MarketAsset | None:
    return await session.get(MarketAsset, ticker)


async def fetch_assets(session: AsyncSession) -> list[MarketAsset]:
    return (await session.execute(select(MarketAsset))).scalars().all()


async def erase_asset(session: AsyncSession, asset: MarketAsset) -> MarketAsset:
    await session.delete(asset)
    await session.commit()
    return asset

