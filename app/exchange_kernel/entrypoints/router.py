from fastapi import APIRouter

from exchange_kernel.entrypoints.v1.router import api_v1


http_api = APIRouter()
http_api.include_router(api_v1, prefix="/v1")

