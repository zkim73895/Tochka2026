import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.entrypoints.v1.identity.security import require_identity
from exchange_kernel.entrypoints.v1.portfolio.contracts import TicketDraft
from exchange_kernel.flows.catalog import lookup_market_asset
from exchange_kernel.flows.matching import fetch_profile_orders, find_ticket, revoke_ticket, submit_ticket
from exchange_kernel.renderers.http_payloads import ticket_payload
from exchange_kernel.storage.gateway import provide_session
from exchange_kernel.storage.schema import TicketState, TraderProfile


portfolio_api = APIRouter()


@portfolio_api.get("")
async def my_orders(
    profile: TraderProfile = Depends(require_identity),
    session: AsyncSession = Depends(provide_session),
):
    tickets = await fetch_profile_orders(session, profile)
    return [ticket_payload(ticket) for ticket in tickets]


@portfolio_api.delete("/{order_id}")
async def cancel_order(
    order_id: uuid.UUID,
    profile: TraderProfile = Depends(require_identity),
    session: AsyncSession = Depends(provide_session),
):
    cancelled = await revoke_ticket(session, str(order_id), profile.id)
    if not cancelled:
        raise HTTPException(404, detail="order not found")
    return {"success": True}


@portfolio_api.get("/{order_id}")
async def order_snapshot(
    order_id: uuid.UUID,
    profile: TraderProfile = Depends(require_identity),
    session: AsyncSession = Depends(provide_session),
):
    ticket = await find_ticket(session, str(order_id))
    if ticket is None:
        raise HTTPException(404)
    if ticket.user_id != profile.id:
        raise HTTPException(403)
    return ticket_payload(ticket)


@portfolio_api.post("")
async def place_order(
    payload: TicketDraft,
    profile: TraderProfile = Depends(require_identity),
    session: AsyncSession = Depends(provide_session),
):
    asset = await lookup_market_asset(session, payload.ticker)
    if not asset:
        raise HTTPException(404, detail="ticker unexist")

    ticket = await submit_ticket(session, profile, payload.ticker, payload.direction, payload.qty, payload.price)
    if ticket.status == TicketState.CANCELLED:
        raise HTTPException(422, detail="ORDER CANCELLED")
    return {"success": True, "order_id": str(ticket.id)}

