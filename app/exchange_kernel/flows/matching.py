import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.access.holdings import fetch_holding
from exchange_kernel.access.profiles import fetch_profile
from exchange_kernel.access.tickets import fetch_live_book, fetch_owned_ticket, fetch_profile_tickets, fetch_ticket
from exchange_kernel.access.trades import append_trade
from exchange_kernel.foundation.config import load_config
from exchange_kernel.storage.schema import ExchangeTicket, QuoteSide, TicketState, TraderProfile


async def fetch_profile_orders(session: AsyncSession, profile: TraderProfile) -> list[ExchangeTicket]:
    return await fetch_profile_tickets(session, profile.id)


async def find_ticket(session: AsyncSession, ticket_id: str) -> ExchangeTicket | None:
    return await fetch_ticket(session, uuid.UUID(ticket_id))


async def revoke_ticket(session: AsyncSession, ticket_id: str, profile_id: uuid.UUID) -> ExchangeTicket | None:
    ticket = await fetch_owned_ticket(session, uuid.UUID(ticket_id), profile_id)
    if not ticket:
        return None

    if ticket.status in [TicketState.PARTIALLY_EXECUTED, TicketState.EXECUTED, TicketState.CANCELLED]:
        raise HTTPException(400, "Order executed/partially_executed/cancelled")
    if ticket.price is None:
        raise HTTPException(400, "Order is market")

    config = load_config()
    if ticket.direction == QuoteSide.ASK:
        await release_reserve(session, ticket.user_id, ticket.instrument_ticker, ticket.amount)
    elif ticket.direction == QuoteSide.BID:
        await release_reserve(session, ticket.user_id, config.quote_ticker, ticket.amount * ticket.price)

    ticket.status = TicketState.CANCELLED
    session.add(ticket)
    await session.flush()
    await session.refresh(ticket)
    await session.commit()
    return ticket


async def submit_ticket(
    session: AsyncSession,
    profile: TraderProfile,
    ticker: str,
    side_name: str,
    qty: int,
    price: int | None,
) -> ExchangeTicket:
    if side_name == "BUY":
        return await process_bid_ticket(session, ticker, qty, price, profile)
    return await process_ask_ticket(session, ticker, qty, price, profile)


async def process_bid_ticket(
    session: AsyncSession,
    ticker: str,
    qty: int,
    price: int | None,
    profile: TraderProfile,
) -> ExchangeTicket:
    book = await fetch_live_book(session, ticker, QuoteSide.ASK, qty)
    ticket = ExchangeTicket(
        user_id=profile.id,
        instrument_ticker=ticker,
        amount=qty,
        filled=0,
        price=price,
        direction=QuoteSide.BID,
        status=TicketState.NEW,
    )
    try:
        for resting in book:
            if ticket.amount == 0 or (price is not None and resting.price > price):
                break
            deal_size = min(resting.amount, ticket.amount)
            await settle_bid_against_book(session, resting.user_id, profile.id, ticker, resting.price, deal_size)
            await mark_fill(session, resting, deal_size)
            await mark_fill(session, ticket, deal_size)

        if ticket.status != TicketState.EXECUTED:
            if price is not None:
                config = load_config()
                await reserve_value(session, profile.id, config.quote_ticker, ticket.amount * ticket.price)
            else:
                raise Exception("Not enough orders")

        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        return ticket
    except Exception:
        await session.rollback()
        ticket.amount = qty
        ticket.filled = 0
        ticket.status = TicketState.CANCELLED
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        return ticket


async def process_ask_ticket(
    session: AsyncSession,
    ticker: str,
    qty: int,
    price: int | None,
    profile: TraderProfile,
) -> ExchangeTicket:
    book = await fetch_live_book(session, ticker, QuoteSide.BID, qty)
    ticket = ExchangeTicket(
        user_id=profile.id,
        instrument_ticker=ticker,
        amount=qty,
        filled=0,
        price=price,
        direction=QuoteSide.ASK,
        status=TicketState.NEW,
    )
    try:
        for resting in book:
            if ticket.amount == 0 or (price is not None and resting.price < price):
                break
            deal_size = min(resting.amount, ticket.amount)
            await settle_ask_against_book(session, profile.id, resting.user_id, ticker, resting.price, deal_size)
            await mark_fill(session, resting, deal_size)
            await mark_fill(session, ticket, deal_size)

        if ticket.status != TicketState.EXECUTED:
            if price is not None:
                await reserve_value(session, profile.id, ticker, ticket.amount)
            else:
                raise Exception("Not enough orders")

        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        return ticket
    except Exception:
        await session.rollback()
        ticket.amount = qty
        ticket.filled = 0
        ticket.status = TicketState.CANCELLED
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        return ticket


async def settle_bid_against_book(
    session: AsyncSession,
    seller_id: uuid.UUID,
    buyer_id: uuid.UUID,
    ticker: str,
    price: int,
    amount: int,
) -> None:
    buyer = await fetch_profile(session, buyer_id)
    seller = await fetch_profile(session, seller_id)
    buyer_holding = await fetch_holding(session, buyer_id, ticker)

    if buyer.balance < amount * price:
        raise Exception("Not enough balance")

    await append_trade(session, seller_id, buyer_id, ticker, amount, price)
    seller.balance += amount * price
    buyer.balance -= amount * price
    buyer_holding.quantity += amount
    await session.flush()


async def settle_ask_against_book(
    session: AsyncSession,
    seller_id: uuid.UUID,
    buyer_id: uuid.UUID,
    ticker: str,
    price: int,
    amount: int,
) -> None:
    seller = await fetch_profile(session, seller_id)
    seller_holding = await fetch_holding(session, seller_id, ticker)
    buyer_holding = await fetch_holding(session, buyer_id, ticker)

    if seller_holding.quantity < amount:
        raise Exception("Not enough instruments")

    await append_trade(session, seller_id, buyer_id, ticker, amount, price)
    seller.balance += amount * price
    seller_holding.quantity -= amount
    buyer_holding.quantity += amount
    await session.flush()


async def mark_fill(session: AsyncSession, ticket: ExchangeTicket, amount: int) -> None:
    if ticket.amount < amount:
        raise Exception("Order not enough amount")
    ticket.amount -= amount
    ticket.filled += amount
    ticket.status = TicketState.EXECUTED if ticket.amount == 0 else TicketState.PARTIALLY_EXECUTED
    await session.flush()


async def reserve_value(session: AsyncSession, profile_id: uuid.UUID, ticker: str, amount: int) -> None:
    config = load_config()
    profile = await fetch_profile(session, profile_id)
    if ticker == config.quote_ticker:
        if profile.balance < amount:
            raise Exception("User not enough balance/instruments")
        profile.balance -= amount
        await session.flush()
        return

    holding = await fetch_holding(session, profile_id, ticker)
    if holding.quantity < amount:
        raise Exception("User not enough balance/instruments")
    holding.quantity -= amount
    await session.flush()


async def release_reserve(session: AsyncSession, profile_id: uuid.UUID, ticker: str, amount: int) -> None:
    config = load_config()
    if ticker == config.quote_ticker:
        profile = await fetch_profile(session, profile_id)
        profile.balance += amount
        await session.flush()
        return

    holding = await fetch_holding(session, profile_id, ticker)
    holding.quantity += amount
    await session.flush()

