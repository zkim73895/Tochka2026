from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.entrypoints.v1.backoffice.handlers import backoffice_api
from exchange_kernel.entrypoints.v1.identity.security import require_identity
from exchange_kernel.entrypoints.v1.marketdata.handlers import marketdata_api
from exchange_kernel.entrypoints.v1.portfolio.handlers import portfolio_api
from exchange_kernel.flows.wallets import collect_balance_view
from exchange_kernel.storage.gateway import provide_session
from exchange_kernel.storage.schema import TraderProfile


api_v1 = APIRouter()
api_v1.include_router(marketdata_api, prefix="/public")
api_v1.include_router(backoffice_api, prefix="/admin")
api_v1.include_router(portfolio_api, prefix="/order")


@api_v1.get("/balance")
async def get_balance(
    profile: TraderProfile = Depends(require_identity),
    session: AsyncSession = Depends(provide_session),
):
    return await collect_balance_view(session, profile)

