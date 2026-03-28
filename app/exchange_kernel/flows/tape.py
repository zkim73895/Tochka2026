from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.access.trades import fetch_recent_trades


async def read_tape(session: AsyncSession, ticker: str, limit: int = 10):
    return await fetch_recent_trades(session, ticker, limit)

