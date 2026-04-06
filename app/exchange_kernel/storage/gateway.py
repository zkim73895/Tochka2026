from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from exchange_kernel.foundation.config import load_config


config = load_config()
engine = create_async_engine(
    config.database_dsn,
    echo=False,
    pool_size=10,
    max_overflow=15,
    pool_recycle=1800,
    pool_pre_ping=True,
    pool_timeout=30,
)
session_hub = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def provide_session() -> AsyncIterator[AsyncSession]:
    async with session_hub() as session:
        yield session
