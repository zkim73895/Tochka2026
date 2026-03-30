import uuid

from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.storage.schema import ExchangeTicket, QuoteSide, TicketState


async def fetch_ticket(session: AsyncSession, ticket_id: uuid.UUID) -> ExchangeTicket | None:
    return await session.get(ExchangeTicket, ticket_id)


async def fetch_owned_ticket(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    profile_id: uuid.UUID,
) -> ExchangeTicket | None:
    query = select(ExchangeTicket).where(
        ExchangeTicket.id == ticket_id,
        ExchangeTicket.user_id == profile_id,
    )
    return (await session.execute(query)).scalars().first()


async def fetch_profile_tickets(session: AsyncSession, profile_id: uuid.UUID) -> list[ExchangeTicket]:
    query = select(ExchangeTicket).where(ExchangeTicket.user_id == profile_id)
    return (await session.execute(query)).scalars().all()


async def fetch_live_book(
    session: AsyncSession,
    ticker: str,
    side: QuoteSide,
    limit: int = 10,
) -> list[ExchangeTicket]:
    query = (
        select(ExchangeTicket)
        .where(
            ExchangeTicket.instrument_ticker == ticker,
            ExchangeTicket.direction == side,
            ExchangeTicket.status.in_([TicketState.NEW, TicketState.PARTIALLY_EXECUTED]),
        )
        .order_by(
            desc(ExchangeTicket.price) if side == QuoteSide.BID else asc(ExchangeTicket.price),
            ExchangeTicket.created_at,
        )
        .limit(limit)
    )
    return (await session.execute(query)).scalars().all()

