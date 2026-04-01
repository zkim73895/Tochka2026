from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.access.assets import fetch_asset
from exchange_kernel.access.holdings import fetch_holding, fetch_holdings
from exchange_kernel.access.profiles import fetch_profile
from exchange_kernel.access.tickets import fetch_profile_tickets
from exchange_kernel.foundation.config import load_config
from exchange_kernel.storage.schema import QuoteSide, TicketState, TraderProfile


async def collect_balance_view(session: AsyncSession, profile: TraderProfile) -> dict:
    config = load_config()
    holdings = await fetch_holdings(session, profile.id)
    snapshot = {item.instrument_ticker: item.quantity for item in holdings}
    snapshot[config.quote_ticker] = profile.balance

    tickets = await fetch_profile_tickets(session, profile.id)
    for ticket in tickets:
        if ticket.status not in [TicketState.NEW, TicketState.PARTIALLY_EXECUTED]:
            continue
        if ticket.direction == QuoteSide.ASK:
            snapshot[ticket.instrument_ticker] += ticket.amount
        elif ticket.direction == QuoteSide.BID:
            snapshot[config.quote_ticker] += ticket.amount * ticket.price
    return snapshot


async def apply_balance_delta(session: AsyncSession, profile_id, ticker: str, amount: int):
    config = load_config()
    profile = await fetch_profile(session, profile_id)
    if ticker == config.quote_ticker:
        next_value = profile.balance + amount
        if next_value < 0:
            raise HTTPException(status_code=400, detail="Balance must be >= 0")
        profile.balance = next_value
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        return profile

    holding = await fetch_holding(session, profile.id, ticker)
    if holding is None:
        asset = await fetch_asset(session, ticker)
        if not asset:
            raise HTTPException(status_code=404, detail="Instrument not found")
        raise HTTPException(status_code=400, detail="Balance must be >= 0")

    next_quantity = holding.quantity + amount
    if next_quantity < 0:
        raise HTTPException(status_code=400, detail="Balance must be >= 0")
    holding.quantity = next_quantity
    session.add(holding)
    await session.commit()
    await session.refresh(profile)
    return profile

