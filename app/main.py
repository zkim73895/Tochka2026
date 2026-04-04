import logging

from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

from exchange_kernel.entrypoints.router import http_api

load_dotenv(".env")

logging.basicConfig(level=logging.ERROR)

app = FastAPI()
app.include_router(http_api, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
