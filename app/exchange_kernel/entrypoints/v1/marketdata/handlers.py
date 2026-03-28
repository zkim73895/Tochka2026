from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.access.tickets import fetch_live_book
from exchange_kernel.entrypoints.deps import load_asset
from exchange_kernel.entrypoints.v1.identity.security import issue_api_key
from exchange_kernel.entrypoints.v1.marketdata.contracts import RegistrationForm
from exchange_kernel.flows.catalog import list_market_assets
from exchange_kernel.flows.identity import onboard_profile
from exchange_kernel.flows.tape import read_tape
from exchange_kernel.renderers.http_payloads import asset_payload, orderbook_payload, trade_payload
from exchange_kernel.storage.gateway import provide_session
from exchange_kernel.storage.schema import MarketAsset, QuoteSide


marketdata_api = APIRouter()


@marketdata_api.post("/register")
async def register_profile(
    payload: RegistrationForm,
    session: AsyncSession = Depends(provide_session),
):
    profile, api_key = await onboard_profile(session, payload.name)
    return {
        "name": profile.name,
        "id": str(profile.id),
        "role": profile.role.name,
        "api_key": api_key,
    }


@marketdata_api.get("/instrument")
async def list_assets(session: AsyncSession = Depends(provide_session)):
    assets = await list_market_assets(session)
    return [asset_payload(asset) for asset in assets]


@marketdata_api.get("/orderbook/{ticker}")
async def get_orderbook(
    asset: MarketAsset = Depends(load_asset),
    limit: int = 10,
    session: AsyncSession = Depends(provide_session),
):
    bids = await fetch_live_book(session, asset.ticker, QuoteSide.BID, limit)
    asks = await fetch_live_book(session, asset.ticker, QuoteSide.ASK, limit)
    return {
        "bid_levels": orderbook_payload(bids, QuoteSide.BID),
        "ask_levels": orderbook_payload(asks, QuoteSide.ASK),
    }


@marketdata_api.get("/transactions/{ticker}")
async def get_trade_tape(
    asset: MarketAsset = Depends(load_asset),
    limit: int = 10,
    session: AsyncSession = Depends(provide_session),
):
    trades = await read_tape(session, asset.ticker, limit)
    return [trade_payload(trade) for trade in trades]

