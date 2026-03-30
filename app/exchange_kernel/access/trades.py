from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.storage.schema import TradePrint


async def fetch_recent_trades(
    session: AsyncSession,
    ticker: str,
    limit: int = 10,
) -> list[TradePrint]:
    query = (
        select(TradePrint)
        .where(TradePrint.instrument_ticker == ticker)
        .order_by(desc(TradePrint.timestamp))
        .limit(limit)
    )
    return (await session.execute(query)).scalars().all()


async def append_trade(
    session: AsyncSession,
    seller_id,
    buyer_id,
    ticker: str,
    amount: int,
    price: float,
) -> TradePrint:
    trade = TradePrint(
        user_from_id=seller_id,
        user_to_id=buyer_id,
        instrument_ticker=ticker,
        amount=amount,
        price=price,
    )
    session.add(trade)
    await session.flush()
    return trade

