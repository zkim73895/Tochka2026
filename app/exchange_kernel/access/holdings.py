import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.storage.schema import AssetLedger


async def fetch_holdings(
    session: AsyncSession,
    profile_id: uuid.UUID,
    ticker: str | None = None,
) -> list[AssetLedger]:
    query = select(AssetLedger).where(AssetLedger.user_id == profile_id)
    if ticker is not None:
        query = query.where(AssetLedger.instrument_ticker == ticker)
    return (await session.execute(query)).scalars().all()


async def fetch_holding(session: AsyncSession, profile_id: uuid.UUID, ticker: str) -> AssetLedger | None:
    query = select(AssetLedger).where(
        AssetLedger.user_id == profile_id,
        AssetLedger.instrument_ticker == ticker,
    )
    return (await session.execute(query)).scalars().first()

