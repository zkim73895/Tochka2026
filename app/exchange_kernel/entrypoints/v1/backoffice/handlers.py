from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.entrypoints.deps import load_asset, load_profile
from exchange_kernel.entrypoints.v1.backoffice.contracts import AssetDraft, BalancePatch
from exchange_kernel.entrypoints.v1.identity.security import require_backoffice
from exchange_kernel.foundation.config import load_config
from exchange_kernel.flows.catalog import create_market_asset, lookup_market_asset, remove_market_asset
from exchange_kernel.flows.identity import resolve_profile
from exchange_kernel.flows.wallets import apply_balance_delta
from exchange_kernel.access.profiles import drop_profile
from exchange_kernel.storage.gateway import provide_session
from exchange_kernel.storage.schema import MarketAsset, TraderProfile


backoffice_api = APIRouter()


@backoffice_api.post("/instrument")
async def create_instrument_record(
    payload: AssetDraft,
    profile: TraderProfile = Depends(require_backoffice),
    session: AsyncSession = Depends(provide_session),
):
    await create_market_asset(session, payload.name, payload.ticker)
    return {"success": True}


@backoffice_api.post("/balance/deposit")
async def deposit_balance(
    payload: BalancePatch,
    profile: TraderProfile = Depends(require_backoffice),
    session: AsyncSession = Depends(provide_session),
):
    config = load_config()
    subject = await resolve_profile(session, str(payload.user_id))
    if not subject:
        raise HTTPException(status_code=404, detail="User not found")

    if await lookup_market_asset(session, payload.ticker) is None and payload.ticker != config.quote_ticker:
        raise HTTPException(status_code=404, detail="Instrument not found")

    await apply_balance_delta(session, payload.user_id, payload.ticker, payload.amount)
    return {"success": True}


@backoffice_api.post("/balance/withdraw")
async def withdraw_balance(
    payload: BalancePatch,
    profile: TraderProfile = Depends(require_backoffice),
    session: AsyncSession = Depends(provide_session),
):
    config = load_config()
    subject = await resolve_profile(session, str(payload.user_id))
    if not subject:
        raise HTTPException(status_code=404, detail="User not found")

    if await lookup_market_asset(session, payload.ticker) is None and payload.ticker != config.quote_ticker:
        raise HTTPException(status_code=404, detail="Instrument not found")

    await apply_balance_delta(session, payload.user_id, payload.ticker, -1 * payload.amount)
    return {"success": True}


@backoffice_api.delete("/user/{user_id}")
async def delete_user(
    victim: TraderProfile = Depends(load_profile),
    profile: TraderProfile = Depends(require_backoffice),
    session: AsyncSession = Depends(provide_session),
):
    removed = await drop_profile(session, victim)
    return {
        "id": removed.id,
        "name": removed.name,
        "role": removed.role.name,
        "api_key": removed.api_key,
    }


@backoffice_api.delete("/instrument/{ticker}")
async def delete_instrument_record(
    asset: MarketAsset = Depends(load_asset),
    profile: TraderProfile = Depends(require_backoffice),
    session: AsyncSession = Depends(provide_session),
):
    await remove_market_asset(session, asset)
    return {"success": True}
