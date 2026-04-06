from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class RuntimeConfig:
    pg_user: str
    pg_password: str
    pg_host: str
    pg_port: str
    pg_db: str
    jwt_secret: str
    jwt_algorithm: str
    token_ttl_minutes: int
    quote_ticker: str

    @property
    def database_dsn(self) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )


@lru_cache
def load_config() -> RuntimeConfig:
    load_dotenv(".env")
    return RuntimeConfig(
        pg_user=os.getenv("POSTGRES_USER", ""),
        pg_password=os.getenv("POSTGRES_PASSWORD", ""),
        pg_host=os.getenv("POSTGRES_HOST", ""),
        pg_port=os.getenv("POSTGRES_PORT", ""),
        pg_db=os.getenv("POSTGRES_DB", ""),
        jwt_secret=os.getenv("SECRET_KEY", ""),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        token_ttl_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "0")),
        quote_ticker=os.getenv("BASE_INSTRUMENT_TICKER", "RUB"),
    )
